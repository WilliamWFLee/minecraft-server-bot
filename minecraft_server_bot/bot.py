import discord

from .embeds import offline_embed, online_embed
from .server import ServerManager
from .views import ServerOfflineView, ServerOnlineView


def initialise_bot(*, server_path):
    intents = discord.Intents.default()
    bot = discord.Bot(intents=intents)

    @bot.slash_command(
        description="Generates a fancy textbox with buttons to control the server",
    )
    async def embed(ctx: discord.ApplicationContext):
        server_manager = ServerManager(server_path=server_path)
        if await server_manager.is_server_open(timeout=1):
            embed = online_embed()
            view = ServerOnlineView(server_manager)
        else:
            embed = offline_embed()
            view = ServerOfflineView(server_manager)
        await ctx.respond(embed=embed, view=view)

    return bot
