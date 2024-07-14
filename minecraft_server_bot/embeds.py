import discord


def generate_server_embed(*, status: str, description: str):
    embed = discord.Embed(title="Minecraft Server", description=description)
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


def please_wait_embed():
    return generate_server_embed(status="Action Pending", description="⏳ Please wait")


def get_embed_for_state(state: str):
    return {
        "stopped": offline_embed,
        "starting": starting_embed,
        "started": online_embed,
        "stopping": stopping_embed,
    }[state]()
