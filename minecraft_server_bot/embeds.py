import datetime as dt

import discord

from .mods import Mod
from .server import ServerInfo


def generate_base_embed():
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    embed = discord.Embed()
    embed.set_footer(text=f"Last updated: {timestamp}")

    return embed


def get_embed_for_server(*, state: str, server_info: ServerInfo):
    status, description = {
        "stopped": ("Offline", "⛔ Server is offline"),
        "starting": ("Starting", "⏳ Server is being started"),
        "started": ("Online", "🚀 Server is online"),
        "stopping": ("Stopping", "⏳ Server is being stopped"),
        "pending": ("Pending", "⏳ Please wait"),
    }[state]

    embed = generate_base_embed()
    embed.title = "Minecraft Server"
    embed.description = description
    embed.add_field(name="Status", value=status, inline=True)
    if state == "started":
        embed.add_field(
            name="Player count",
            value=server_info.player_count,
            inline=True,
        )
        if server_info.player_count:
            embed.add_field(
                name="Players",
                value="\n".join([f"- {player}" for player in server_info.players]),
                inline=False,
            )

    return embed


def get_mods_embed(mods: list[Mod]):
    embed = generate_base_embed()
    embed.title = "Mods"
    for mod in mods:
        embed.add_field(
            name=mod.name,
            value=f"Version: {mod.version}",
            inline=False,
        )

    return embed
