import asyncio

import discord
from tortoise.queryset import QuerySet

from minecraft_server_bot.messages import fetch_message_from_record

from .models import BotMessage
from .server import ServerManager
from .view import ServerView


class ServerController:
    def __init__(
        self, *, server_manager: ServerManager, client: discord.Client
    ) -> None:
        self.client = client
        self.server_manager: ServerManager = server_manager
        self.view: ServerView

    async def initialise(self) -> None:
        self.view = ServerView(self)
        await self.server_manager.initialise()
        await self.render_and_update(self.server_manager.state)

    @property
    async def all_controls_messages(self) -> QuerySet[BotMessage]:
        return await BotMessage.filter(message_type="controls")

    async def render_and_update(self, state: str):
        await self.view.render(state)
        messages: list[discord.Message] = filter(
            None,
            await asyncio.gather(
                *(
                    fetch_message_from_record(record=record, client=self.client)
                    for record in await self.all_controls_messages
                )
            ),
        )
        await asyncio.gather(
            *(
                message.edit(view=self.view, embed=self.view.embed)
                for message in messages
            )
        )

    async def handle_start(self) -> None:
        await self.render_and_update("pending")

        await self.server_manager.start_server()
        await self.render_and_update("starting")

        if await self.server_manager.wait_for_server_start():
            await self.render_and_update("started")
        else:
            await self.render_and_update("stopped")

    async def handle_stop(self) -> None:
        await self.render_and_update("pending")

        await self.server_manager.stop_server()
        await self.render_and_update("stopping")

        if await self.server_manager.wait_for_server_stop():
            await self.render_and_update("stopped")
        else:
            await self.render_and_update("started")

    async def handle_restart(self):
        await self.render_and_update("pending")

        await self.server_manager.stop_server()
        await self.render_and_update("stopping")

        if not await self.server_manager.wait_for_server_stop():
            await self.render_and_update("started")
            return

        await self.server_manager.start_server()
        await self.render_and_update("starting")

        if await self.server_manager.wait_for_server_start():
            await self.render_and_update("started")
        else:
            await self.render_and_update("stopped")
