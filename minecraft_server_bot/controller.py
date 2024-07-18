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
        await self.view.send_state(self.server_manager.state)

    async def handle_start(self, interaction: discord.Interaction):
        await self._update_view("pending", interaction)
        await self.server_manager.start_server()
        await self._update_view("starting", interaction)
        if await self.server_manager.wait_for_server_start():
            await self._update_view("started", interaction)
        else:
            await self._update_view("stopped", interaction)

    async def handle_stop(self, interaction: discord.Interaction):
        await self._update_view("pending", interaction)
        await self.server_manager.stop_server()
        await self._update_view("stopping", interaction)
        if await self.server_manager.wait_for_server_stop():
            await self._update_view("stopped", interaction)
        else:
            await self._update_view("started", interaction)

    async def handle_restart(self, interaction: discord.Interaction):
        await self._update_view("pending", interaction)
        await self.server_manager.stop_server()
        await self._update_view("stopping", interaction)
        if await self.server_manager.wait_for_server_stop():
            await self.server_manager.start_server()
            await self._update_view("starting", interaction)
            if await self.server_manager.wait_for_server_start():
                await self._update_view("started", interaction)
            else:
                await self._update_view("stopped", interaction)
        else:
            await self._update_view("started", interaction)

    async def _update_view(self, state: str, interaction: discord.Interaction):
        await self.view.send_state(state)
        await self.view.update_messages(current_interaction=interaction)
