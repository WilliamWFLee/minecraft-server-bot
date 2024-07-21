import asyncio
import re
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

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

    def __init__(self, *, server_path: Path | str, server_manager: "ServerManager"):
        self.server_path = Path(server_path)
        self.server_manager = server_manager
        self.player_count = 0
        self.players = []
        self._read_server_properties()

    @staticmethod
    def _load_file_contents(server_path: Path | str):
        with open(server_path) as f:
            return f.read()

    def get_mods(self) -> list[Mod]:
        return sorted(
            (
                Mod.from_jar(path)
                for path in self.server_path.joinpath("mods").glob("*.jar")
            ),
            key=lambda mod: mod.name,
        )

    async def update(self) -> None:
        await self._update_player_info()

    async def _update_player_info(self) -> str:
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
            self.port = 25565


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
        self._state_listeners: list[StateListener] = []

        if not session_name:
            session_name = "minecraft_server"

        if tmux_manager is None:
            self.tmux_manager = TmuxManager(session_name=session_name)

    async def initialise(self) -> None:
        await self.info.update()
        await self._initialise_state()

    def add_state_listener(self, coro: StateListener) -> None:
        self._state_listeners.append(coro)

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

    async def _dispatch_state_update(self) -> None:
        await asyncio.gather(
            *(listener(self.state) for listener in self._state_listeners)
        )

    async def _update_state(self, state: str) -> None:
        self.state = state
        await self._dispatch_state_update()

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
