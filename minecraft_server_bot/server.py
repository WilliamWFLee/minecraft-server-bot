import asyncio
import re
from functools import wraps
from pathlib import Path

from discord.ext import tasks

from .ipify import get_ip
from .mixins import UpdateDispatcherMixin
from .mods import Mod
from .tmux import TmuxManager


class ServerState(UpdateDispatcherMixin):
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    @classmethod
    async def create(cls, host: str, port: int) -> "ServerState":
        self = cls(host, port)
        return self

    async def online(self):
        return await self._test_connection()

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

    async def _test_connection(self) -> bool:
        try:
            _, writer = await asyncio.open_connection(self.host, self.port)
        except ConnectionError:
            return False
        else:
            writer.close()
            await writer.wait_closed()
            return True

    async def _server_started_test_loop(self) -> None:
        while not await self.online():
            await asyncio.sleep(0.1)

    async def _server_stopped_test_loop(self) -> None:
        while await self.online():
            await asyncio.sleep(0.1)


class ServerConsole:
    def __init__(
        self,
        *,
        session_name: str,
        server_path: Path,
        executable_filename: str,
        server_state: ServerState,
    ):
        self.tmux_manager = TmuxManager(session_name=session_name)
        self.server_path = server_path
        self.executable_filename = executable_filename
        self.server_state = server_state

    @staticmethod
    def _require_offline(coro):
        @wraps(coro)
        async def inner(self, *args, **kwargs):
            if await self.server_state.online():
                return False
            await coro(self, *args, **kwargs)
            return True

        return inner

    @staticmethod
    def _require_online(coro):
        @wraps(coro)
        async def inner(self, *args, **kwargs) -> bool:
            if not await self.server_state.online():
                return False
            await coro(self, *args, **kwargs)
            return True

        return inner

    @_require_offline
    async def start_command(self):
        self.tmux_manager.send_command(f"cd {self.server_path}")
        self.tmux_manager.send_command(f"./{self.executable_filename}")

    @_require_online
    async def stop_command(self):
        self.tmux_manager.send_command("stop")

    @_require_online
    async def list_players(self):
        self.tmux_manager.send_command("list")


class ServerConfiguration:
    SERVER_HOST_KEY = "server-ip"
    SERVER_PORT_KEY = "server-port"
    SERVER_HOST_REGEX = re.compile(rf"(?<={SERVER_HOST_KEY}=).+")
    SERVER_PORT_REGEX = re.compile(rf"(?<={SERVER_PORT_KEY}=)\d+")

    def __init__(self, *, server_path: Path):
        self.server_path = server_path
        self.load()

    def get_mods(self) -> list[Mod]:
        return sorted(
            (
                Mod.from_jar(path)
                for path in self.server_path.joinpath("mods").glob("*.jar")
            ),
            key=lambda mod: mod.name,
        )

    def load(self) -> None:
        properties_path = self.server_path.joinpath("server.properties")
        with open(properties_path) as f:
            contents = f.read()
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


class ServerInfo(UpdateDispatcherMixin):
    PLAYER_INFO_REGEX = re.compile(
        r"(?:There are \d+ of a max of \d+ players online:)"
        r"((?:\s+)(?P<player_list>\w+(,\s+\w+)*))?"
    )

    def __init__(self, *, server_path: Path, server_console: ServerConsole) -> None:
        super().__init__()
        self.server_path: Path = server_path
        self.server_console: ServerConsole = server_console
        self.player_count: int = 0
        self.players: list[str] = []
        self.public_ip: str | None = None

    @classmethod
    async def create(
        cls,
        *,
        server_path: Path,
        server_console: ServerConsole,
        server_state: ServerState,
    ) -> "ServerInfo":
        self = cls(server_path=server_path, server_console=server_console)
        if await server_state.online():
            await self.update_public_ip()
        self._update_players_task.start()
        return self

    @tasks.loop(seconds=5)
    async def _update_players_task(self):
        if await self.update_player_info():
            await self._dispatch_update()

    async def update_public_ip(self) -> None:
        try:
            self.public_ip = await get_ip()
        except Exception:
            self.public_ip = None

    async def update_player_info(self) -> None:
        players = None
        if await self.server_console.list_players():
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

    def _latest_log_lines(self) -> str:
        with open(self.server_path.joinpath("logs", "latest.log")) as file:
            return file.readlines()


class ServerManager(UpdateDispatcherMixin):
    def __init__(
        self,
        *,
        server_state: ServerState,
        server_console: ServerConsole,
    ):
        super().__init__()
        self.previous_state: str | None = None
        self.state: str | None = None
        self.server_state: ServerState = server_state
        self.server_console: ServerConsole = server_console
        self._state_lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def create(
        cls,
        server_state: ServerState,
        server_console: ServerConsole,
    ) -> "ServerManager":
        self = cls(server_state=server_state, server_console=server_console)
        self._update_state_task.start()
        return self

    @staticmethod
    def _with_state_lock(coro):
        @wraps(coro)
        async def inner(self, *args, **kwargs):
            async with self._state_lock:
                return await coro(self, *args, **kwargs)

        return inner

    @_with_state_lock
    async def start_server(self) -> None:
        await self._update_state("pending")
        if not await self.server_state.online():
            await self.server_console.start_command()
            await self._update_state("starting")
        if await self.server_state.wait_for_server_start():
            await self._update_state("started")
        else:
            await self._update_state("stopped")

    @_with_state_lock
    async def stop_server(self) -> None:
        await self._update_state("pending")
        if await self.server_state.online():
            await self.server_console.stop_command()
            await self._update_state("stopping")
        if await self.server_state.wait_for_server_stop():
            await self._update_state("stopped")
        else:
            await self._update_state("started")

    @_with_state_lock
    async def restart_server(self) -> None:
        await self._update_state("pending")
        if await self.server_state.online():
            await self.server_console.stop_command()
            await self._update_state("stopping")
        if await self.server_state.wait_for_server_stop():
            await self._update_state("stopped")
            await self.server_console.start_command()
            await self._update_state("starting")
            if await self.server_state.wait_for_server_start():
                await self._update_state("started")
            else:
                await self._update_state("stopped")
        else:
            await self._update_state("started")

    @tasks.loop(seconds=0.1)
    @_with_state_lock
    async def _update_state_task(self) -> None:
        if await self.server_state.online():
            await self._update_state("started")
        else:
            await self._update_state("stopped")

    async def _update_state(self, state: str) -> None:
        self.previous_state = self.state
        self.state = state
        if self.previous_state != state:
            await self._dispatch_update()
