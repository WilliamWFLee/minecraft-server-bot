import discord

from .embeds import offline_embed, online_embed, starting_embed
from .server import ServerManager


class ServerView(discord.ui.View):
    def __init__(self, server_manager: ServerManager):
        super().__init__(timeout=None)
        self.server_manager = server_manager

    @discord.ui.button(
        label="Start",
        style=discord.ButtonStyle.primary,
        custom_id="start_button",
    )
    async def start_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        embed = starting_embed()
        await interaction.edit(embed=embed, view=self)

        await self.server_manager.run_server_start()
        await self.server_manager.wait_for_server_start()

        embed = online_embed()
        await interaction.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Stop",
        style=discord.ButtonStyle.danger,
        custom_id="stop_button",
    )
    async def stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = starting_embed()
        await interaction.edit(embed=embed, view=self)

        await self.server_manager.run_server_stop()
        await self.server_manager.wait_for_server_stop()

        embed = offline_embed()
        await interaction.edit(embed=embed, view=self)
