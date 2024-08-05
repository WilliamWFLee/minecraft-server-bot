import asyncio
from collections.abc import Callable
from typing import Coroutine

from discord import Any

ListenerType = Callable[["UpdateDispatcherMixin"], Coroutine[Any, Any, None]]


class UpdateDispatcherMixin:
    def __init__(self):
        self._listeners: list[ListenerType] = []

    def add_listener(self, listener: ListenerType) -> None:
        self._listeners.append(listener)

    async def _dispatch_update(self) -> None:
        await asyncio.gather(*(listener(self) for listener in self._listeners))
