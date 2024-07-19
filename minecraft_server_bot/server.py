import asyncio
import re
from pathlib import Path

from .tmux import TmuxManager


class ServerConfiguration:
    SERVER_HOST_KEY = "server-ip"
    SERVER_PORT_KEY = "server-port"
    SERVER_HOST_REGEX = re.compile(rf"(?<={SERVER_HOST_KEY}=).+")
    SERVER_PORT_REGEX = re.compile(rf"(?<={SERVER_PORT_KEY}=)\d+")

    def __init__(self, *, server_path: Path | str):
        self.server_path = Path(server_path)
        self._file_contents = self._load_file_contents(
            self.server_path.joinpath("server.properties")
        )

    @staticmethod
    def _load_file_contents(server_path: Path | str):
        with open(server_path) as f:
            return f.read()

    @property
    def host(self) -> str:
        match = self.SERVER_HOST_REGEX.search(self._file_contents)
        if match:
            return match.group(0)
        else:
            return "127.0.0.1"

    @property
    def port(self) -> int:
        match = self.SERVER_PORT_REGEX.search(self._file_contents)
        if match:
            return int(match.group(0))
        else:
            return 25565


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

    async def _set_state(self, state: str) -> None:
        self._state = state
        await self._dispatch_event(state)

    async def _dispatch_event(self, state: str) -> None:
        for listener in self._listeners:
            await listener(state)

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

    async def restart_server(self) -> None:
        await self.stop_server()
        await self.start_server()

    async def initialise(self) -> None:
        await self._fetch_state()
