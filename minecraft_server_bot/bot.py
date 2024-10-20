import asyncio
from functools import wraps
from pathlib import Path

import discord
from tortoise import transactions

from .controller import ServerController
from .database import initialise_database
from .embeds import get_mods_embed
from .messages import delete_existing_guild_message
from .models import BotMessage


class BotApplication:
    def __init__(
        self,
        *,
        server_path: Path | str,
        executable_filename: str,
        session_name: str | None = None,
        database_config: dict,
        max_wait_for_online: int = 30,
    ):
        self.server_path: Path = server_path
        self.executable_filename: str = executable_filename
        self.session_name: str | None = session_name
        self.database_config: dict = database_config
        self.max_wait_for_online = max_wait_for_online
        self._ready: asyncio.Event = asyncio.Event()
        self._initialise_bot()

    def _initialise_bot(self):
        intents = discord.Intents.default()
        self.client = discord.Bot(intents=intents)

        @staticmethod
        def _wait_for_ready(coro):
            @wraps(coro)
            async def inner(ctx: discord.ApplicationContext, *args, **kwargs):
                if not self._ready.is_set():
                    await ctx.defer()
                    await self._ready.wait()
                await coro(ctx, *args, **kwargs)

            return inner

        @self.client.event
        async def on_ready():
            await initialise_database(self.database_config)
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name="/controls",
            )
            self.controller = await ServerController.create(
                client=self.client,
                session_name=self.session_name,
                server_path=self.server_path,
                executable_filename=self.executable_filename,
                max_wait_for_online=self.max_wait_for_online,
            )
            self.client.add_view(self.controller.view)
            await self.client.change_presence(activity=activity)
            await self.controller.wait_until_ready()
            self._ready.set()

        @self.client.slash_command(
            name="controls",
            description="Generates a fancy textbox with buttons to control the server",
        )
        @_wait_for_ready
        async def controls(ctx: discord.ApplicationContext):
            await ctx.respond(
                embed=self.controller.view.embed,
                view=self.controller.view,
            )
            message = await ctx.interaction.original_response()
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

        @self.client.slash_command(
            name="mods",
            description="Shows the mods loaded on the server",
        )
        @_wait_for_ready
        async def mods(ctx: discord.ApplicationContext):
            mods = self.controller.server_configuration.get_mods()
            if not mods:
                await ctx.respond("There are no mods loaded.")
            else:
                await ctx.respond(embed=get_mods_embed(mods))

    def run(self, *args, **kwargs):
        self.client.run(*args, **kwargs)
