from pathlib import Path

import discord

from .embeds import get_embed_for_state
from .server import ServerManager
from .view import ServerView


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

    @bot.event
    async def on_connect():
        await bot.change_presence(activity=activity)

    @bot.event
    async def on_ready():
        await server_manager.initialise()
        bot.add_view(ServerView(server_manager))

    @bot.slash_command(
        description="Generates a fancy textbox with buttons to control the server",
        contexts={discord.InteractionContextType.guild},
    )
    async def controls(ctx: discord.ApplicationContext):
        if not ctx.bot.is_ready():
            await ctx.defer()
            await ctx.bot.wait_until_ready()
        embed = get_embed_for_state(server_manager.state)
        await ctx.respond(embed=embed, view=ServerView(server_manager))

    return bot
