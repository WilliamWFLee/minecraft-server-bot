import asyncio
from pathlib import Path

from .tmux import TmuxManager


class ServerManager:
    def __init__(
        self, *, server_path: Path | str, host: str = "127.0.0.1", port: int = 25565
    ):
        self.host = host
        self.port = port
        self.server_path = server_path
        self.tmux_manager = TmuxManager(session_name="minecraft_server")

    async def wait_for_server_start(self) -> None:
        while True:
            try:
                await asyncio.open_connection(self.host, self.port)
            except ConnectionRefusedError:
                await asyncio.sleep(0.1)
            else:
                return

    async def wait_for_server_stop(self) -> None:
        while True:
            try:
                await asyncio.open_connection(self.host, self.port)
            except ConnectionRefusedError:
                return
            else:
                await asyncio.sleep(0.1)

    async def is_server_open(self, *, timeout: int = 30) -> bool:
        try:
            await asyncio.wait_for(self.wait_for_server_start(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def is_server_close(self, *, timeout: int = 30) -> bool:
        try:
            await asyncio.wait_for(self.wait_for_server_stop(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def run_server_start(self) -> None:
        if await self.is_server_close(timeout=1):
            self.tmux_manager.send_command(f"cd {self.server_path}")
            self.tmux_manager.send_command("./run.sh")

    async def run_server_stop(self) -> None:
        if await self.is_server_open(timeout=1):
            self.tmux_manager.send_command("stop")
