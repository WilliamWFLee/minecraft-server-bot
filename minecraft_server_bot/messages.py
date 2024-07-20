import discord

from .models import BotMessage


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
