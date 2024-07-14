import asyncio

import discord

from .embeds import get_embed_for_state, please_wait_embed
from .server import ServerManager


class ServerView(discord.ui.View):
    def __init__(self, server_manager: ServerManager):
        super().__init__(timeout=None)
        self.server_manager: ServerManager = server_manager
        self._messages: set[discord.Message] = set()
        self.server_manager.listener(self.server_state_listener)

    async def server_state_listener(self, state: str) -> None:
        embed = get_embed_for_state(state)
        for message in self._messages:
            await message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Start",
        style=discord.ButtonStyle.primary,
        custom_id="start_button",
    )
    async def start_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ):
        self._messages.add(interaction.message)
        await interaction.edit(embed=please_wait_embed(), view=self)
        await self.server_manager.start_server()

    @discord.ui.button(
        label="Stop",
        style=discord.ButtonStyle.danger,
        custom_id="stop_button",
    )
    async def stop_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ):
        self._messages.add(interaction.message)
        await interaction.edit(embed=please_wait_embed(), view=self)
        await self.server_manager.stop_server()
