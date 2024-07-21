import discord

from .models import BotMessage


async def fetch_message_from_record(
    *,
    record: BotMessage,
    client: discord.Client,
) -> discord.Message | None:
    guild = client.get_guild(record.guild_id)
    if guild is None:
        return None
    channel = guild.get_channel_or_thread(record.channel_id)
    if channel is None:
        return None
    try:
        return await channel.fetch_message(record.message_id)
    except discord.NotFound:
        return None


async def delete_existing_guild_message(
    *,
    guild: discord.Guild,
    message_type: str,
):
    record = await BotMessage.filter(
        guild_id=guild.id,
        message_type=message_type,
    ).first()
    if record is not None:
        channel = await guild.fetch_channel(record.channel_id)
        existing_message = await channel.fetch_message(record.message_id)
        await existing_message.delete()
        await record.delete()
