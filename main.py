#!/usr/bin/env python3

import os
from pathlib import Path

import discord
import dotenv

from embeds import offline_embed, online_embed
from server import ServerManager
from views import ServerOfflineView, ServerOnlineView

dotenv.load_dotenv()

token = os.environ.get("BOT_TOKEN")
if token is None:
    raise Exception("BOT_TOKEN environment variable is not defined")

dir = Path(os.environ.get("SERVER_PATH", "~/server"))
try:
    dir = dir.expanduser().resolve(strict=True)
except FileNotFoundError:
    raise Exception(f"Server directory does not exist: '{dir}'") from None

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)


@bot.slash_command(
    description="Generates a fancy textbox with buttons to control the server",
)
async def embed(ctx: discord.ApplicationContext):
    server_manager = ServerManager(dir=dir)
    if await server_manager.is_server_open(timeout=1):
        embed = online_embed()
        view = ServerOnlineView(server_manager)
    else:
        embed = offline_embed()
        view = ServerOfflineView(server_manager)
    await ctx.respond(embed=embed, view=view)


bot.run(token)
