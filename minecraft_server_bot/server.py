import asyncio
from pathlib import Path

import libtmux


class ServerManager:
    def __init__(
        self, *, server_path: Path | str, host: str = "127.0.0.1", port: int = 25565
    ):
        self.host = host
        self.port = port
        self.server_path = server_path
        self.tmux_server = libtmux.Server()

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

    def start_tmux_session(self) -> None:
        self.tmux_server.cmd("new-session", "-d", "-s", "minecraft_server")

    @property
    def tmux_session(self) -> libtmux.Session | None:
        return self.tmux_server.sessions.get(name="minecraft_server")

    @property
    def tmux_window(self) -> libtmux.Window | None:
        return self.tmux_session.windows[0]

    @property
    def tmux_pane(self) -> libtmux.Pane | None:
        return self.tmux_window.panes[0]

    def send_terminal_command(self, command: str) -> None:
        self.tmux_pane.send_keys(command)

    async def run_server_start(self) -> None:
        self.start_tmux_session()
        if await self.is_server_close(timeout=1):
            self.send_terminal_command(f"cd {self.server_path}")
            self.send_terminal_command("./run.sh")

    async def run_server_stop(self) -> None:
        self.start_tmux_session()
        if await self.is_server_open(timeout=1):
            self.send_terminal_command("stop")
