from typing import TYPE_CHECKING

import discord

from .embeds import get_embed_for_state

if TYPE_CHECKING:
    from .controller import ServerController


class ServerView(discord.ui.View):
    def __init__(self, controller: "ServerController"):
        super().__init__(timeout=None)
        self._messages: set[discord.Message] = set()
        self.controller = controller
        self.embed = None

    async def send_state(self, state: str) -> "ServerView":
        self.embed = get_embed_for_state(state)
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

    async def update_messages(
        self,
        current_interaction: discord.Interaction | None = None,
    ) -> "ServerView":
        for message in self._messages:
            if current_interaction and current_interaction.message == message:
                continue
            await message.edit(embed=self.embed, view=self)
        await current_interaction.edit(embed=self.embed, view=self)

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
        await self.controller.handle_start(interaction)

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
        await self.controller.handle_stop(interaction)

    @discord.ui.button(
        label="Restart",
        style=discord.ButtonStyle.secondary,
        custom_id="restart_button",
    )
    async def restart_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ):
        self._messages.add(interaction.message)
        await self.controller.handle_restart(interaction)
