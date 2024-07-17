#!/usr/bin/env python3

import os
from pathlib import Path

import dotenv

from minecraft_server_bot import initialise_bot

dotenv.load_dotenv()


def main():
    token = os.environ.get("BOT_TOKEN")
    if token is None:
        raise Exception("BOT_TOKEN environment variable is not defined")

    server_path = os.environ.get("SERVER_PATH")
    if not server_path:
        server_path = "~/minecraft_server"
    try:
        server_path = Path(server_path).expanduser().resolve(strict=True)
    except FileNotFoundError:
        raise Exception(f"Server directory does not exist: '{server_path}'") from None

    executable_filename = os.environ.get("EXECUTABLE_FILENAME")
    if not executable_filename:
        executable_filename = "run.sh"
    if not os.access(server_path.joinpath(executable_filename), os.X_OK):
        raise Exception(f"Could not find '{executable_filename}' in server directory")

    session_name = os.environ.get("SESSION_NAME")
    bot = initialise_bot(
        server_path=server_path,
        executable_filename=executable_filename,
        session_name=session_name,
    )
    bot.run(token)


if __name__ == "__main__":
    main()
