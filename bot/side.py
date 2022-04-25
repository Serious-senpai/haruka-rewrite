from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
import discord
from discord import app_commands

if TYPE_CHECKING:
    import haruka
    from lib.image import ImageClient


class SideClient(discord.Client):
    """Haruka v2 implementation"""

    if TYPE_CHECKING:
        core: haruka.Haruka
        image: ImageClient
        session: aiohttp.ClientSession
        token: str

    def __init__(self, core: haruka.Haruka, token: str) -> None:
        self.core = core
        self.token = token
        super().__init__(intents=core.intents)

        self.tree = app_commands.CommandTree(self)
        self.tree.on_error = core.tree.on_error

    async def start(self) -> None:
        await self.core.wait_until_ready()
        await self.__initialize_state()
        await super().start(self.token)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    async def __initialize_state(self) -> None:
        self.image = self.core.image
        self.session = self.core.session
