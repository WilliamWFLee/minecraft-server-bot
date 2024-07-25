import asyncio
import re
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from discord.ext import tasks

from .ipify import get_ip
from .mods import Mod
from .tmux import TmuxManager

StateListener = Callable[[str], Coroutine[Any, Any, None]]


class ServerInfo:
    SERVER_HOST_KEY = "server-ip"
    SERVER_PORT_KEY = "server-port"
    SERVER_HOST_REGEX = re.compile(rf"(?<={SERVER_HOST_KEY}=).+")
    SERVER_PORT_REGEX = re.compile(rf"(?<={SERVER_PORT_KEY}=)\d+")
    PLAYER_INFO_REGEX = re.compile(
        r"(?:There are )"
        r"(?P<player_count>\d+)(?: of a max of \d+ players online:)"
        r"((?:\s+)(?P<player_list>\w+(,\s+\w+)*))?"
    )
    DEFAULT_PORT = 25565

    def __init__(self, *, server_path: Path | str, server_manager: "ServerManager"):
        self.server_path = Path(server_path)
        self.server_manager = server_manager
        self.player_count = 0
        self.players = []
        self.public_ip = None
        self._read_server_properties()

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

    async def update(self, *scopes: list[str]) -> None:
        if "players" in scopes:
            await self._update_player_info()
        if "address" in scopes:
            await self._update_public_ip()

    @staticmethod
    def _load_file_contents(server_path: Path | str):
        with open(server_path) as f:
            return f.read()

    async def _update_player_info(self) -> None:
        if await self.server_manager.send_server_command("list"):
            for line in reversed(self._latest_log_lines()):
                match = self.PLAYER_INFO_REGEX.search(line)
                if not match:
                    continue
                self.player_count = int(match.group("player_count"))
                if self.player_count:
                    self.players = [
                        player.strip()
                        for player in match.group("player_list").split(",")
                    ]
                else:
                    self.players = []
                break
        else:
            self.player_count = 0
            self.players = []

    async def _update_public_ip(self) -> None:
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


class ServerManager:
    def __init__(
        self,
        *,
        server_path: Path | str,
        executable_filename: str,
        tmux_manager: TmuxManager | None = None,
        session_name: str | None = None,
    ):
        self.server_path = Path(server_path)
        self.executable_filename = executable_filename
        self.state = None
        self.info = ServerInfo(server_path=self.server_path, server_manager=self)
        self._state_lock = asyncio.Lock()
        self._listeners: list[StateListener] = []

        if not session_name:
            session_name = "minecraft_server"

        if tmux_manager is None:
            self.tmux_manager = TmuxManager(session_name=session_name)

    async def initialise(self) -> None:
        await self.info.update("players", "address")
        await self._initialise_state()
        self.refresh_state_task.start()

    def add_listener(self, coro: StateListener) -> None:
        self._listeners.append(coro)

    @tasks.loop(seconds=1)
    async def refresh_state_task(self):
        await self.info.update("players")
        await self._dispatch_update()

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

    async def server_started(self) -> bool:
        return await self.wait_for_server_start(timeout=1)

    async def server_stopped(self) -> bool:
        return await self.wait_for_server_stop(timeout=1)

    async def start_server(self) -> None:
        await self._update_state("pending")
        if await self.server_stopped():
            self.tmux_manager.send_command(f"cd {self.server_path}")
            self.tmux_manager.send_command(f"./{self.executable_filename}")
            await self._update_state("starting")
        if await self.wait_for_server_start():
            await self._update_state("started")
        else:
            await self._update_state("stopped")

    async def stop_server(self) -> None:
        await self._update_state("pending")
        if await self.server_started():
            self.tmux_manager.send_command("stop")
            await self._update_state("stopping")
        if await self.wait_for_server_stop():
            await self._update_state("stopped")
        else:
            await self._update_state("started")

    async def restart_server(self) -> None:
        await self._update_state("pending")
        if await self.server_started():
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
        if await self.server_stopped():
            return False
        self.tmux_manager.send_command(command)
        return True

    async def _update_state(self, state: str) -> None:
        self.state = state
        if self.state == "started":
            await self.info.update("address")
        await self._dispatch_update()

    async def _dispatch_update(self) -> None:
        await asyncio.gather(*(listener() for listener in self._listeners))

    async def _test_connection(self) -> None:
        await asyncio.open_connection(self.info.host, self.info.port)

    async def _server_started_test_loop(self) -> None:
        while True:
            try:
                await self._test_connection()
            except ConnectionRefusedError:
                await asyncio.sleep(0.1)
            else:
                return

    async def _server_stopped_test_loop(self) -> None:
        while True:
            try:
                await self._test_connection()
            except ConnectionRefusedError:
                return
            else:
                await asyncio.sleep(0.1)

    async def _initialise_state(self) -> None:
        if await self.server_started():
            self.state = "started"
        else:
            self.state = "stopped"
