import asyncio
from typing import List, Optional, Union

import discord


class SelectMenu(discord.ui.Select):
    def __init__(self, *, placeholder: str, options: List[discord.SelectOption]) -> None:
        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self._future: asyncio.Future = self._loop.create_future()
        super().__init__(placeholder=placeholder, options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.stop()
        self._future.set_result(self.values.pop())

    async def result(self) -> str:
        return await self._future


class DropdownMenu(discord.ui.View):

    children: List[SelectMenu]

    def __init__(self, *, timeout: Optional[float] = 120.0) -> None:
        self.message: Optional[Union[discord.Message, discord.WebhookMessage]] = None
        super().__init__(timeout=timeout)

    def stop(self) -> asyncio.Task:
        super().stop()
        return asyncio.create_task(self._do_stop())

    async def _do_stop(self) -> None:
        if self.message:
            await self.message.edit("This request was received. Please wait for me a bit...", view=None)

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit("This request has timed out.", view=None)
            for item in self.children:
                item._future.set_exception(asyncio.TimeoutError)

    async def send(self, target: Union[discord.abc.Messageable, discord.Webhook], *args, **kwargs) -> None:
        kwargs.pop("view", None)
        self.message = await target.send(*args, **kwargs, view=self)
