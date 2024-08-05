import asyncio
import re
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from discord.ext import tasks

from .ipify import get_ip
from .mixins import UpdateDispatcherMixin
from .mods import Mod
from .tmux import TmuxManager

ServerManagerListener = Callable[[], Coroutine[Any, Any, None]]
ServerInfoListener = Callable[[], Coroutine[Any, Any, None]]


class ServerInfo(UpdateDispatcherMixin):
    SERVER_HOST_KEY = "server-ip"
    SERVER_PORT_KEY = "server-port"
    SERVER_HOST_REGEX = re.compile(rf"(?<={SERVER_HOST_KEY}=).+")
    SERVER_PORT_REGEX = re.compile(rf"(?<={SERVER_PORT_KEY}=)\d+")
    PLAYER_INFO_REGEX = re.compile(
        r"(?:There are \d+ of a max of \d+ players online:)"
        r"((?:\s+)(?P<player_list>\w+(,\s+\w+)*))?"
    )
    DEFAULT_PORT = 25565

    def __init__(self, *, server_path: Path | str, server_manager: "ServerManager"):
        super().__init__()
        self.server_path = Path(server_path)
        self.server_manager = server_manager
        self.player_count = 0
        self.players = []
        self.public_ip = None
        self._read_server_properties()
        if not self.update_players_task.is_running():
            self.update_players_task.start()

    @tasks.loop(seconds=5)
    async def update_players_task(self):
        if await self.update_player_info():
            await self._dispatch_update()

    @property
    def public_address(self) -> str:
        if self.public_ip is None:
            return None
        elif self.port == self.DEFAULT_PORT:
            return f"{self.public_ip}"
        else:
            return f"{self.public_ip}:{self.port}"

    def get_mods(self) -> list[Mod]:
        return sorted(
            (
                Mod.from_jar(path)
                for path in self.server_path.joinpath("mods").glob("*.jar")
            ),
            key=lambda mod: mod.name,
        )

    async def update(self, *scopes: list[str]) -> bool:
        if "players" in scopes:
            await self.update_player_info()
        if "address" in scopes:
            await self.update_public_ip()

    @staticmethod
    def _load_file_contents(server_path: Path | str):
        with open(server_path) as f:
            return f.read()

    async def update_player_info(self) -> None:
        players = None
        if await self.server_manager.send_server_command("list"):
            for line in reversed(self._latest_log_lines()):
                match = self.PLAYER_INFO_REGEX.search(line)
                if not match:
                    continue
                if (player_list := match.group("player_list")) is None:
                    players = []
                else:
                    players = [player.strip() for player in player_list.split(",")]
                break
        if players is None:
            players = []

        if sorted(players) != sorted(self.players):
            self.player_count = len(players)
            self.players = players
            return True
        return False

    async def update_public_ip(self) -> None:
        try:
            self.public_ip = await get_ip()
        except Exception:
            self.public_ip = None

    def _latest_log_lines(self) -> str:
        with open(self.server_path.joinpath("logs", "latest.log")) as file:
            return file.readlines()

    def _read_server_properties(self) -> None:
        contents = self._load_file_contents(
            self.server_path.joinpath("server.properties")
        )
        match = self.SERVER_HOST_REGEX.search(contents)
        if match:
            self.host = match.group(0)
        else:
            self.host = "127.0.0.1"

        match = self.SERVER_PORT_REGEX.search(contents)
        if match:
            self.port = int(match.group(0))
        else:
            self.port = self.DEFAULT_PORT


class ServerManager(UpdateDispatcherMixin):
    def __init__(
        self,
        *,
        server_path: Path | str,
        executable_filename: str,
        tmux_manager: TmuxManager | None = None,
        session_name: str | None = None,
    ):
        super().__init__()
        self.server_path = Path(server_path)
        self.executable_filename: str = executable_filename
        self.state: str | None = None
        self.server_online: bool = False
        self.info = ServerInfo(server_path=self.server_path, server_manager=self)
        self.info.add_listener(self._server_info_handler)
        self._state_lock = asyncio.Lock()

        if not session_name:
            session_name = "minecraft_server"

        if tmux_manager is None:
            self.tmux_manager = TmuxManager(session_name=session_name)

    async def initialise(self) -> None:
        await self._initialise_state()
        await self.info.update_player_info()
        await self.info.update_public_ip()
        if not self.update_server_online_task.is_running():
            self.update_server_online_task.start()

    @tasks.loop(seconds=0.1)
    async def update_server_online_task(self):
        self.server_online = await self._test_connection()

    async def wait_for_server_start(self, *, timeout: int = 30) -> bool:
        try:
            await asyncio.wait_for(self._server_started_test_loop(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_for_server_stop(self, *, timeout: int = 15) -> bool:
        try:
            await asyncio.wait_for(self._server_stopped_test_loop(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def start_server(self) -> None:
        await self._update_state("pending")
        if not self.server_online:
            self.tmux_manager.send_command(f"cd {self.server_path}")
            self.tmux_manager.send_command(f"./{self.executable_filename}")
            await self._update_state("starting")
        if await self.wait_for_server_start():
            await self._update_state("started")
        else:
            await self._update_state("stopped")

    async def stop_server(self) -> None:
        await self._update_state("pending")
        if self.server_online:
            self.tmux_manager.send_command("stop")
            await self._update_state("stopping")
        if await self.wait_for_server_stop():
            await self._update_state("stopped")
        else:
            await self._update_state("started")

    async def restart_server(self) -> None:
        await self._update_state("pending")
        if await self.server_online:
            self.tmux_manager.send_command("stop")
            await self._update_state("stopping")
        if await self.wait_for_server_stop():
            await self._update_state("stopped")
            self.tmux_manager.send_command(f"cd {self.server_path}")
            self.tmux_manager.send_command(f"./{self.executable_filename}")
            await self._update_state("starting")
            if await self.wait_for_server_start():
                await self._update_state("started")
            else:
                await self._update_state("stopped")
        else:
            await self._update_state("started")

    async def send_server_command(self, command: str) -> bool:
        if not self.server_online:
            return False
        self.tmux_manager.send_command(command)
        return True

    async def _server_info_handler(self, server_info: ServerInfo) -> None:
        await self._dispatch_update()

    async def _update_state(self, state: str) -> None:
        self.state = state
        if self.state == "started":
            await self.info.update_public_ip()
        await self._dispatch_update()

    async def _test_connection(self) -> bool:
        try:
            _, writer = await asyncio.open_connection(self.info.host, self.info.port)
        except ConnectionError:
            return False
        else:
            writer.close()
            await writer.wait_closed()
            return True

    async def _server_started_test_loop(self) -> None:
        while not self.server_online:
            await asyncio.sleep(0.1)

    async def _server_stopped_test_loop(self) -> None:
        while self.server_online:
            await asyncio.sleep(0.1)

    async def _initialise_state(self) -> None:
        if self.server_online:
            self.state = "started"
        else:
            self.state = "stopped"
