import datetime as dt

import discord

from .mods import Mod


def generate_base_embed():
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    embed = discord.Embed()
    embed.set_footer(text=f"Last updated: {timestamp}")

    return embed


def generate_server_embed(*, status: str, description: str):
    embed = generate_base_embed()
    embed.title = "Minecraft Server"
    embed.description = description
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Player count", value=0, inline=True)
    embed.add_field(name="Players", value="thing", inline=True)

    return embed


def offline_embed():
    return generate_server_embed(
        status="Offline",
        description="⛔ Server is offline",
    )


def starting_embed():
    return generate_server_embed(
        status="Starting",
        description="⏳ Server is being started",
    )


def online_embed():
    return generate_server_embed(
        status="Online",
        description="🚀 Server is online",
    )


def stopping_embed():
    return generate_server_embed(
        status="Stopping",
        description="⏳ Server is being stopped",
    )


def pending_embed():
    return generate_server_embed(status="Pending", description="⏳ Please wait")


def get_embed_for_server_state(state: str):
    return {
        "stopped": offline_embed,
        "starting": starting_embed,
        "started": online_embed,
        "stopping": stopping_embed,
        "pending": pending_embed,
    }[state]()


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
