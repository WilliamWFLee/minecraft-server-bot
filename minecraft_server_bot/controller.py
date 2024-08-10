import asyncio
from pathlib import Path

import discord
from tortoise.queryset import QuerySet

from minecraft_server_bot.messages import fetch_message_from_record

from .models import BotMessage
from .server import (
    ServerConfiguration,
    ServerConsole,
    ServerInfo,
    ServerManager,
    ServerState,
)
from .view import ServerView


class ServerController:
    def __init__(self, *, client: discord.Client) -> None:
        self.client: discord.Client = client
        self._ready: asyncio.Event = asyncio.Event()
        self.server_configuration: ServerConfiguration
        self.server_state: ServerState
        self.server_console: ServerConsole
        self.server_info: ServerInfo
        self.server_manager: ServerManager
        self.view: ServerView

    @classmethod
    async def create(
        cls,
        *,
        client: discord.Client,
        session_name: str,
        server_path: Path | str,
        executable_filename: str
    ) -> "ServerController":
        server_path = Path(server_path)

        self = cls(client=client)
        self.server_configuration = ServerConfiguration(server_path=server_path)
        self.server_configuration.load()
        self.server_state = await ServerState.create(
            host=self.server_configuration.host,
            port=self.server_configuration.port,
        )
        self.server_console = ServerConsole(
            session_name=session_name,
            server_path=server_path,
            executable_filename=executable_filename,
            server_state=self.server_state,
        )
        self.server_info = await ServerInfo.create(
            server_path=server_path,
            server_state=self.server_state,
            server_console=self.server_console,
        )
        self.server_manager = await ServerManager.create(
            server_state=self.server_state,
            server_console=self.server_console,
        )
        self.view = ServerView(self)

        self.server_manager.add_listener(self.server_listener)
        self.server_info.add_listener(self.server_listener)
        return self

    async def server_listener(self, _) -> None:
        if self.server_manager.state == "started":
            await self.server_info.update_public_ip()
        await self._render_and_update_view()

    async def handle_start(self) -> None:
        await self.server_manager.start_server()

    async def handle_stop(self) -> None:
        await self.server_manager.stop_server()

    async def handle_restart(self) -> None:
        await self.server_manager.restart_server()

    async def wait_until_ready(self) -> None:
        await self._ready.wait()

    @property
    async def _all_controls_messages(self) -> QuerySet[BotMessage]:
        return await BotMessage.filter(message_type="controls")

    async def _render_and_update_view(self):
        await self.view.render()
        self._ready.set()
        messages: list[discord.Message] = filter(
            None,
            await asyncio.gather(
                *(
                    fetch_message_from_record(record=record, client=self.client)
                    for record in await self._all_controls_messages
                )
            ),
        )
        await asyncio.gather(
            *(
                message.edit(view=self.view, embed=self.view.embed)
                for message in messages
            )
        )
