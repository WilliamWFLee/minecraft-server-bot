import os

import dotenv

dotenv.load_dotenv()

database_name = os.environ.get("DATABASE_NAME")
if not database_name:
    database_name = "minecraft_server_bot"

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "database": f"{database_name}",
            },
        }
    },
    "apps": {
        "models": {
            "models": ["minecraft_server_bot.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

__all__ = ["TORTOISE_ORM"]
