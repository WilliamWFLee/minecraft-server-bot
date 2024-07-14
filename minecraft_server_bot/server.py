import asyncio
from functools import wraps
from pathlib import Path

from .tmux import TmuxManager


class ServerManager:
    def __init__(
        self,
        *,
        server_path: Path | str,
        executable_filename: str,
        host: str = "127.0.0.1",
        port: int = 25565,
        tmux_manager: TmuxManager | None = None,
        session_name: str | None = None,
    ):
        self.server_path = server_path
        self.executable_filename = executable_filename
        self.host = host
        self.port = port
        self.state = None
        self._lock = asyncio.Lock()

        if not session_name:
            session_name = "minecraft_server"

        if tmux_manager is None:
            self.tmux_manager = TmuxManager(session_name=session_name)

    @staticmethod
    def with_lock(coro):
        @wraps(coro)
        async def inner(self: "ServerManager", *args, **kwargs):
            async with self._lock:
                return await coro(self, *args, **kwargs)

        return inner

    async def _fetch_state(self) -> None:
        if await self.server_started():
            self.state = "started"
        else:
            self.state = "stopped"

    async def _test_connection(self) -> None:
        await asyncio.open_connection(self.host, self.port)

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

    async def wait_for_server_stop(self, *, timeout: int = 30) -> bool:
        try:
            await asyncio.wait_for(self._server_stopped_test_loop(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def server_started(self) -> bool:
        return await self.wait_for_server_start(timeout=1)

    async def server_stopped(self) -> bool:
        return await self.wait_for_server_stop(timeout=1)

    @with_lock
    async def start_server(self) -> bool:
        if await self.server_stopped():
            self.state = "starting"

            self.tmux_manager.send_command(f"cd {self.server_path}")
            self.tmux_manager.send_command(f"./{self.executable_filename}")

            result = await self.wait_for_server_start()
            if result:
                self.state = "started"
            else:
                self.state = "stopped"
            return result
        return True

    @with_lock
    async def stop_server(self) -> bool:
        if await self.server_started():
            self.state = "stopping"

            self.tmux_manager.send_command("stop")

            result = await self.wait_for_server_stop()
            if result:
                self.state = "stopped"
            else:
                self.state = "started"
            return result
        return True

    async def initialise(self) -> None:
        await self._fetch_state()
