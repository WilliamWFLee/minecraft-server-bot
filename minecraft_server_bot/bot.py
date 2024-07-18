from pathlib import Path

import discord

from .controller import ServerController
from .server import ServerManager


def initialise_bot(
    *,
    server_path: Path | str,
    executable_filename: str,
    session_name: str = None,
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
        bot.add_view(controller.view)

    @bot.slash_command(
        description="Generates a fancy textbox with buttons to control the server",
        contexts={discord.InteractionContextType.guild},
    )
    async def controls(ctx: discord.ApplicationContext):
        if not ctx.bot.is_ready():
            await ctx.defer()
            await ctx.bot.wait_until_ready()
        await ctx.respond(embed=controller.view.embed, view=controller.view)

    return bot
