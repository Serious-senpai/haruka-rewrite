import asyncio
from typing import List, Optional, Union

import discord


class SelectMenu(discord.ui.Select):
    def __init__(self, *, placeholder: str, options: List[discord.SelectOption]) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.future: asyncio.Future = self.loop.create_future()
        super().__init__(placeholder=placeholder, options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.stop()
        self.future.set_result(self.values[0])

    async def result(self) -> str:
        return await self.future


class DropdownView(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        self.message: Optional[discord.Message] = None
        super().__init__(*args, **kwargs)
        asyncio.create_task(self._when_stopped())

    async def _when_stopped(self) -> None:
        _timed_out: bool = await self.wait()
        if self.message:
            if _timed_out:
                await self.message.edit("This request has timed out.", view=None)
            else:
                await self.message.edit("This request was received. Please wait for me a bit...", view=None)

    async def send(self, target: Union[discord.abc.Messageable, discord.Webhook], *args, **kwargs) -> None:
        kwargs.pop("view", None)
        self.message: Union[discord.Message, discord.WebhookMessage] = await target.send(*args, **kwargs, view=self)
