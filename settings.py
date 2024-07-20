TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "database": "minecraft_server_bot",
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
