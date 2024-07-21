from pathlib import Path

import discord
from tortoise import transactions

from .controller import ServerController
from .database import initialise_database
from .messages import delete_existing_guild_message
from .models import BotMessage
from .server import ServerManager


def initialise_bot(
    *,
    server_path: Path | str,
    executable_filename: str,
    session_name: str = None,
    database_config: dict,
):
    activity = discord.Activity(type=discord.ActivityType.listening, name="/controls")
    intents = discord.Intents.default()
    bot = discord.Bot(intents=intents)
    server_manager = ServerManager(
        server_path=server_path,
        executable_filename=executable_filename,
        session_name=session_name,
    )
    controller = ServerController(server_manager)

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=activity)
        await controller.initialise()
        await initialise_database(database_config)
        bot.add_view(controller.view)

    @bot.slash_command(
        description="Generates a fancy textbox with buttons to control the server",
        contexts={discord.InteractionContextType.guild},
    )
    async def controls(ctx: discord.ApplicationContext):
        if not ctx.bot.is_ready():
            await ctx.defer()
            await ctx.bot.wait_until_ready()

        interaction = await ctx.respond(
            embed=controller.view.embed, view=controller.view
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

    @bot.slash_command(
        description="Shows the mods loaded on the server",
        contexts={discord.InteractionContextType.guild},
    )
    async def mods(ctx: discord.ApplicationContext):
        if not ctx.bot.is_ready():
            await ctx.defer()
            await ctx.bot.wait_until_ready()
        embed = discord.Embed(title="Mods")
        if not server_manager.info.mods:
            await ctx.respond("There are no mods loaded.")
        else:
            for mod in server_manager.info.mods:
                embed.add_field(
                    name=mod.name,
                    value=f"Version: {mod.version}",
                    inline=False,
                )
            await ctx.respond(embed=embed)

    return bot
