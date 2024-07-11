#!/usr/bin/env python3

import os

import discord
import dotenv

dotenv.load_dotenv()

token = os.environ.get("BOT_TOKEN")
if token is None:
    raise Exception("Bot token is missing from environment")

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)


@bot.slash_command()
async def start(ctx: discord.ApplicationContext):
    await ctx.respond("test")


bot.run(token)
