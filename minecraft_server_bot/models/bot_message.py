from tortoise import fields
from tortoise.models import Model


class BotMessage(Model):
    guild_id = fields.BigIntField(unique=True)
    channel_id = fields.BigIntField(unique=True)
    message_id = fields.BigIntField(unique=True)
    message_type = fields.CharField(255)

    class Meta:
        table = "bot_messages"
