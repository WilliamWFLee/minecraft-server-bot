import discord


def generate_server_embed(*, description: str):
    embed = discord.Embed(title="Minecraft Server", description=description)
    embed.add_field(name="Status", value="Offline", inline=True)
    embed.add_field(name="Player count", value=0, inline=True)
    embed.add_field(name="Players", value="thing", inline=True)

    return embed


def offline_embed():
    return generate_server_embed(description="⛔ Server is offline")


def starting_embed():
    return generate_server_embed(description="⏳ Server is being started")


def online_embed():
    return generate_server_embed(description="✅ Server is online")


def stopping_embed():
    return generate_server_embed(description="⏳ Server is being stopped")
