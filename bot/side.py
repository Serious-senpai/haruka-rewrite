from __future__ import annotations

import asyncio
import io
from typing import List, Dict, Optional, TYPE_CHECKING

import aiohttp
import discord

from lib import trees
from mixins import ClientMixin
if TYPE_CHECKING:
    import haruka
    from _types import Context, Interaction
    from lib.image import ImageClient


class SideClient(discord.Client, ClientMixin):
    """Haruka v2 implementation"""

    if TYPE_CHECKING:
        _command_count: Dict[str, List[Context]]  # This will always be empty though
        _slash_command_count: Dict[str, List[Interaction]]
        _owner: discord.User

        core: haruka.Haruka
        image: ImageClient
        logfile: io.TextIOWrapper
        session: aiohttp.ClientSession
        token: str

    def __init__(self, core: haruka.Haruka, token: str) -> None:
        self.core = core
        self.token = token
        self.logfile = core.logfile
        self._command_count = {}
        self._slash_command_count = {}

        intents = discord.Intents.default()
        intents.bans = False
        intents.typing = False
        intents.integrations = False
        intents.invites = False
        intents.webhooks = False

        super().__init__(intents=intents, activity=discord.Game("Restarting..."))

        self.tree = trees.SideClientTree(self)

    async def start(self) -> None:
        await self.core.wait_until_ready()
        await self.__initialize_state()
        await super().start(self.token)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    async def setup_hook(self) -> None:
        async def _change_activity_after_booting() -> None:
            await self.wait_until_ready()
            await asyncio.sleep(5.0)
            await self.core.owner_ready.wait()
            await self.change_presence(activity=discord.Game("with my senpai!"))

        self.loop.create_task(_change_activity_after_booting(), name="Change activity: v2")

    async def __initialize_state(self) -> None:
        self.image = self.core.image
        self.session = self.core.session

    @property
    def owner(self) -> Optional[discord.User]:
        if not self.core.owner_ready.is_set():
            return

        try:
            return self._owner
        except AttributeError:
            self._owner = discord.User(state=self._connection, data=self.core.owner_data)

        return self._owner
