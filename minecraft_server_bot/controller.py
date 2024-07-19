import discord

from .server import ServerManager
from .view import ServerView


class ServerController:
    def __init__(self, server_manager: ServerManager) -> None:
        self.server_manager: ServerManager = server_manager
        self.view: ServerView

    async def initialise(self) -> None:
        self.view = ServerView(self)
        await self.server_manager.initialise()
        await self.view.render(self.server_manager.state)

    async def handle_start(self, interaction: discord.Interaction) -> None:
        await self.view.render("pending", interaction)

        await self.server_manager.start_server()
        await self.view.render("starting", interaction)

        if await self.server_manager.wait_for_server_start():
            await self.view.render("started", interaction)
        else:
            await self.view.render("stopped", interaction)

    async def handle_stop(self, interaction: discord.Interaction) -> None:
        await self.view.render("pending", interaction)

        await self.server_manager.stop_server()
        await self.view.render("stopping", interaction)

        if await self.server_manager.wait_for_server_stop():
            await self.view.render("stopped", interaction)
        else:
            await self.view.render("started", interaction)

    async def handle_restart(self, interaction: discord.Interaction):
        await self.view.render("pending", interaction)

        await self.server_manager.stop_server()
        await self.view.render("stopping", interaction)

        if not await self.server_manager.wait_for_server_stop():
            await self.view.render("started", interaction)
            return

        await self.server_manager.start_server()
        await self.view.render("starting", interaction)

        if await self.server_manager.wait_for_server_start():
            await self.view.render("started", interaction)
        else:
            await self.view.render("stopped", interaction)
