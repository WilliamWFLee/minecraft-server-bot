from pathlib import Path

import discord

from .embeds import offline_embed, online_embed
from .server import ServerManager
from .view import ServerView


def initialise_bot(
    *,
    server_path: Path | str,
    executable_filename: str,
    session_name: str = None,
):
    intents = discord.Intents.default()
    bot = discord.Bot(intents=intents)
    server_manager = ServerManager(
        server_path=server_path,
        executable_filename=executable_filename,
        session_name=session_name,
    )

    @bot.event
    async def on_ready():
        await server_manager.initialise()
        bot.add_view(ServerView(server_manager))

    @bot.slash_command(
        description="Generates a fancy textbox with buttons to control the server",
        contexts={discord.InteractionContextType.guild},
    )
    async def embed(ctx: discord.ApplicationContext):
        if await server_manager.server_started():
            embed = online_embed()
        else:
            embed = offline_embed()
        await ctx.respond(embed=embed, view=ServerView(server_manager))

    return bot
