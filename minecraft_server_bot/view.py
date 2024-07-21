from typing import TYPE_CHECKING

import discord

from .embeds import get_embed_for_server_state

if TYPE_CHECKING:
    from .controller import ServerController


class ServerView(discord.ui.View):
    def __init__(self, controller: "ServerController"):
        super().__init__(timeout=None)
        self.controller = controller
        self.embed = None

    async def render(self, state: str) -> "ServerView":
        self.embed = get_embed_for_server_state(state)
        buttons_disabled = {
            "stopped": [False, True, True],
            "starting": [True, True, True],
            "started": [True, False, False],
            "stopping": [True, True, True],
            "pending": [True, True, True],
        }[state]
        for custom_id, disabled in zip(
            ["start_button", "stop_button", "restart_button"],
            buttons_disabled,
        ):
            self.get_item(custom_id).disabled = disabled

    @discord.ui.button(
        emoji="🚀",
        label="Start",
        style=discord.ButtonStyle.primary,
        custom_id="start_button",
    )
    async def start_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer()
        await self.controller.handle_start()

    @discord.ui.button(
        emoji="◽",
        label="Stop",
        style=discord.ButtonStyle.danger,
        custom_id="stop_button",
    )
    async def stop_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer()
        await self.controller.handle_stop()

    @discord.ui.button(
        emoji="🔄",
        label="Restart",
        style=discord.ButtonStyle.secondary,
        custom_id="restart_button",
    )
    async def restart_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer()
        await self.controller.handle_restart()
