import discord

from .embeds import offline_embed, online_embed
from .server import ServerManager
from .view import ServerView


def initialise_bot(*, server_path):
    intents = discord.Intents.default()
    bot = discord.Bot(intents=intents)
    server_manager = ServerManager(server_path=server_path)

    @bot.event
    async def on_ready():
        bot.add_view(ServerView(server_manager))

    @bot.slash_command(
        description="Generates a fancy textbox with buttons to control the server",
        contexts={discord.InteractionContextType.guild},
    )
    async def embed(ctx: discord.ApplicationContext):
        if await server_manager.is_server_open(timeout=1):
            embed = online_embed()
        else:
            embed = offline_embed()
        await ctx.respond(embed=embed, view=ServerView(server_manager))

    return bot
