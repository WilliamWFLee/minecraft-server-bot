from tortoise import Tortoise


async def initialise_database(config):
    await Tortoise.init(config=config)
