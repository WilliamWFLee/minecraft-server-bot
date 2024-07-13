import discord

from .embeds import offline_embed, online_embed, starting_embed
from .server import ServerManager


class BaseServerView(discord.ui.View):
    def __init__(self, server_manager: ServerManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_manager = server_manager


class ServerOfflineView(BaseServerView):
    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = starting_embed()
        await interaction.edit(embed=embed, view=ServerActionPendingView())

        await self.server_manager.run_server_start()
        await self.server_manager.is_server_open()

        embed = online_embed()
        await interaction.edit(embed=embed, view=ServerOnlineView(self.server_manager))


class ServerActionPendingView(discord.ui.View):
    @discord.ui.button(label="...", style=discord.ButtonStyle.gray, disabled=True)
    async def pending(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ):
        pass


class ServerOnlineView(BaseServerView):
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = starting_embed()
        await interaction.edit(embed=embed, view=ServerActionPendingView())

        await self.server_manager.run_server_stop()
        await self.server_manager.wait_for_server_stop()

        embed = offline_embed()
        await interaction.edit(embed=embed, view=ServerOfflineView(self.server_manager))
