import asyncio

import discord
from discord.ext import tasks
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
        self.server_manager.add_state_listener(self.server_state_handler)
        self.view: ServerView

    async def initialise(self) -> None:
        self.view = ServerView(self)
        await self.server_manager.initialise()
        await self._render_and_update_view(self.server_manager.state)
        self.refresh_server_state_task.start()

    async def server_state_handler(self, state: str) -> None:
        await self._render_and_update_view(state)

    @tasks.loop(seconds=15)
    async def refresh_server_state_task(self):
        await self.server_manager.info.update()
        await self._render_and_update_view(self.server_manager.state)

    async def handle_start(self) -> None:
        await self.server_manager.start_server()

    async def handle_stop(self) -> None:
        await self.server_manager.stop_server()

    async def handle_restart(self):
        await self.server_manager.restart_server()

    @property
    async def _all_controls_messages(self) -> QuerySet[BotMessage]:
        return await BotMessage.filter(message_type="controls")

    async def _render_and_update_view(self, state: str):
        await self.view.render(state=state, server_info=self.server_manager.info)
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
