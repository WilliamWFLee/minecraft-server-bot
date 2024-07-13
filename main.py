#!/usr/bin/env python3

import os
from pathlib import Path

import dotenv

from minecraft_server_bot import initialise_bot

dotenv.load_dotenv()

token = os.environ.get("BOT_TOKEN")
if token is None:
    raise Exception("BOT_TOKEN environment variable is not defined")

server_path = Path(os.environ.get("SERVER_PATH", "~/server"))
try:
    server_path = server_path.expanduser().resolve(strict=True)
except FileNotFoundError:
    raise Exception(f"Server directory does not exist: '{server_path}'") from None

bot = initialise_bot(server_path=server_path)
bot.run(token)
