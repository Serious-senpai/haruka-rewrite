from __future__ import annotations

import asyncio
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

        intents = discord.Intents.default()
        intents.bans = False
        intents.typing = False
        intents.integrations = False
        intents.invites = False
        intents.webhooks = False

        super().__init__(intents=intents, activity=discord.Game("Restarting..."))

        self.tree = app_commands.CommandTree(self)
        self.tree.on_error = core.tree.on_error

    async def start(self) -> None:
        await self.core.wait_until_ready()
        await self.__initialize_state()
        await super().start(self.token)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    async def setup_hook(self) -> None:
        async def _change_activity_after_booting() -> None:
            await self.wait_until_ready()
            await asyncio.sleep(20.0)
            await self.change_presence(activity=discord.Game("with my senpai!"))

        self.loop.create_task(_change_activity_after_booting(), name="Change activity: v2")

    async def __initialize_state(self) -> None:
        self.image = self.core.image
        self.session = self.core.session
