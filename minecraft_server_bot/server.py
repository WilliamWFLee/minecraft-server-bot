import asyncio
import re
from pathlib import Path

from .mods import Mod
from .tmux import TmuxManager


class ServerConfiguration:
    SERVER_HOST_KEY = "server-ip"
    SERVER_PORT_KEY = "server-port"
    SERVER_HOST_REGEX = re.compile(rf"(?<={SERVER_HOST_KEY}=).+")
    SERVER_PORT_REGEX = re.compile(rf"(?<={SERVER_PORT_KEY}=)\d+")

    def __init__(self, *, server_path: Path | str):
        self.server_path = Path(server_path)
        self._read_server_properties()

    @staticmethod
    def _load_file_contents(server_path: Path | str):
        with open(server_path) as f:
            return f.read()

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
            self.port = 25565


class ServerInfo:
    def __init__(self, *, server_path: Path | str):
        self.server_path = Path(server_path)
        self._mods = []

    @property
    def mods(self) -> list[Mod]:
        return sorted(
            (
                Mod.from_jar(path)
                for path in self.server_path.joinpath("mods").glob("*.jar")
            ),
            key=lambda mod: mod.name,
        )


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
        self.info = ServerInfo(server_path=self.server_path)
        self._config = ServerConfiguration(server_path=self.server_path)

        if not session_name:
            session_name = "minecraft_server"

        if tmux_manager is None:
            self.tmux_manager = TmuxManager(session_name=session_name)

    async def _fetch_state(self) -> None:
        if await self.server_started():
            self.state = "started"
        else:
            self.state = "stopped"

    async def _test_connection(self) -> None:
        await asyncio.open_connection(self._config.host, self._config.port)

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
        if await self.server_stopped():
            self.tmux_manager.send_command(f"cd {self.server_path}")
            self.tmux_manager.send_command(f"./{self.executable_filename}")

    async def stop_server(self) -> None:
        if await self.server_started():
            self.tmux_manager.send_command("stop")

    async def initialise(self) -> None:
        await self._fetch_state()
