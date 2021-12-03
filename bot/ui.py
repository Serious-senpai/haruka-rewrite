import asyncio
import discord
from typing import Optional, Union


class View(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        self.message: Optional[discord.Message] = None
        asyncio.create_task(self._when_stopped())
        super().__init__(*args, **kwargs)

    async def _when_stopped(self) -> None:
        _timed_out: bool = await self.wait()
        if self.message:
            if _timed_out:
                await self.message.edit("This request has timed out.", view=None)
            else:
                await self.message.edit("This request was received. Please wait for me a bit...", view=None)

    async def send(
        self,
        target: Union[discord.abc.Messageable, discord.Webhook],
        *args,
        **kwargs,
    ) -> None:
        kwargs.pop("view", None)
        self.message: Union[discord.Message, discord.WebhookMessage] = await target.send(*args, **kwargs, view=self)
