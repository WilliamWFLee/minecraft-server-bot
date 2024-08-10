from pathlib import Path

import discord
from tortoise import transactions

from .controller import ServerController
from .database import initialise_database
from .embeds import get_mods_embed
from .messages import delete_existing_guild_message
from .models import BotMessage


class BotApplication(discord.Bot):
    def __init__(
        self,
        *,
        server_path: Path | str,
        executable_filename: str,
        session_name: str = None,
        database_config: dict,
    ):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

        self.server_path = server_path
        self.executable_filename = executable_filename
        self.session_name = session_name
        self.database_config = database_config

        self.application_command(
            name="controls",
            description="Generates a fancy textbox with buttons to control the server",
            contexts={discord.InteractionContextType.guild},
        )(self.controls_command)

        self.application_command(
            name="mods",
            description="Shows the mods loaded on the server",
            contexts={discord.InteractionContextType.guild},
        )(self.mods_command)

    async def on_ready(self):
        await initialise_database(self.database_config)
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/controls",
        )
        self.controller = await ServerController.create(
            client=self,
            session_name=self.session_name,
            server_path=self.server_path,
            executable_filename=self.executable_filename,
        )
        self.add_view(self.controller.view)
        await self.change_presence(activity=activity)

    async def controls_command(self, ctx: discord.ApplicationContext):
        if not ctx.bot.is_ready():
            await ctx.defer()
            await ctx.bot.wait_until_ready()

        interaction = await ctx.respond(
            embed=self.controller.view.embed,
            view=self.controller.view,
        )
        message = await interaction.original_response()
        async with transactions.in_transaction():
            await delete_existing_guild_message(
                guild=message.guild,
                message_type="controls",
            )
            await BotMessage.create(
                guild_id=message.guild.id,
                channel_id=message.channel.id,
                message_id=message.id,
                message_type="controls",
            )

    async def mods_command(self, ctx: discord.ApplicationContext):
        if not ctx.bot.is_ready():
            await ctx.defer()
            await ctx.bot.wait_until_ready()

        mods = self.controller.server_configuration.get_mods()
        if not mods:
            await ctx.respond("There are no mods loaded.")
        else:
            await ctx.respond(embed=get_mods_embed(mods))
