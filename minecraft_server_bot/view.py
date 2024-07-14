import asyncio

import discord

from .embeds import offline_embed, online_embed, starting_embed, stopping_embed
from .server import ServerManager


class ServerView(discord.ui.View):
    def __init__(self, server_manager: ServerManager):
        super().__init__(timeout=None)
        self.server_manager = server_manager

    async def update(self, interaction: discord.Interaction = None):
        embed = {
            "stopped": offline_embed,
            "starting": starting_embed,
            "started": online_embed,
            "stopping": stopping_embed,
        }[self.server_manager.state]()

        if interaction is not None:
            await interaction.edit(embed=embed, view=self)

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
        task = asyncio.Task(self.server_manager.start_server())
        await self.update()

        await task
        await self.update(interaction)

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
        task = asyncio.Task(self.server_manager.stop_server())
        await self.update()

        await task
        await self.update(interaction)
