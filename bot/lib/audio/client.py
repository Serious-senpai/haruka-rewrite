from __future__ import annotations

import asyncio
import os
import random
from typing import Dict, Callable, List, Optional, Type, TypeVar, TYPE_CHECKING

import aiohttp
import asyncpg
import discord
from discord import app_commands
from discord.ext import commands

from env import HOST
from .constants import initialize_hosts
from .exceptions import AudioNotFound
from .sources import PartialInvidiousSource, InvidiousSource
if TYPE_CHECKING:
    import haruka
    from _types import Context, Interaction


__all__ = ("AudioClient",)


fetching_in_progress: Dict[str, asyncio.Event] = {}
if TYPE_CHECKING:
    T = TypeVar("T")
    SourceT = TypeVar("SourceT", PartialInvidiousSource, InvidiousSource)


class AudioClient:

    __slots__ = ("bot")
    if TYPE_CHECKING:
        bot: haruka.Haruka

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot

    @property
    def pool(self) -> asyncpg.Pool:
        return self.bot.conn

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session

    async def initialize_hosts(self) -> None:
        hosts = initialize_hosts(self.bot.session)
        self.bot.log("Sorted Invidious instances to:\n" + "\n".join(hosts))

    @staticmethod
    def in_voice(*, slash_command: bool = False) -> Callable[[T], T]:
        """A command check that returns ``True`` if the invoker is
        currently in a voice channel.
        """
        if slash_command:
            async def predicate(interaction: Interaction) -> bool:
                if isinstance(interaction.user, discord.Member):
                    if interaction.user.voice:
                        return True

                await interaction.response.send_message("Please join a voice channel first!")
                return False

            return app_commands.check(predicate)

        else:
            async def predicate(ctx: Context) -> bool:
                if isinstance(ctx.author, discord.Member):
                    if ctx.author.voice:
                        return True

                await ctx.send("Please join a voice channel first!")
                return False

            return commands.check(predicate)

    @staticmethod
    def create_audio_url(track_id: str) -> str:
        """Create an URL to the local audio file of the video with ID
        ``track_id`` which is exposed to the server side.

        Parameters
        -----
        track_id: ``str``
            The track ID

        Returns
        -----
        ``str``
            The created URL

        Raises
        -----
        ``AudioNotFound``
            The local audio file could not be found
        """
        if os.path.isfile(f"./server/audio/{track_id}.mp3"):
            return HOST + f"/audio/{track_id}.mp3"

        raise AudioNotFound(track_id)

    def create_audio_embed(self, source: PartialInvidiousSource) -> discord.Embed:
        """Create an embed displaying the video information and URL
        to the video audio.

        Parameters
        -----
        source: ``PartialInvidiousSource``
            The video source object

        Returns
        -----
        ``discord.Embed``
            The created embed

        Raises
        -----
        ``AudioNotFound``
            The local audio file could not be found
        """
        embed = source.create_embed()
        embed.set_author(
            name="YouTube audio request",
            icon_url=self.bot.user.avatar.url,
        )
        embed.add_field(
            name="Audio URL",
            value=f"[Download]({self.create_audio_url(source.id)})",
            inline=False,
        )
        return embed

    async def fetch(self, track: InvidiousSource) -> Optional[str]:
        """This function is a coroutine

        Download a video audio to the local machine and return its URL.

        Parameters
        -----
        track: ``InvidiousSource``
            The target track.

        Returns
        -----
        Optional[``str``]
            The URL to the audio file, exposed via the server side
        """
        try:
            await fetching_in_progress[track.id].wait()
            try:
                return self.create_audio_url(track.id)
            except AudioNotFound:
                return
        except KeyError:
            fetching_in_progress[track.id] = asyncio.Event()

        url = await track.ensure_source(client=self)
        if not url:
            return

        args = (
            "ffmpeg",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-i", url,
            "-f", "mp3",
            "-vn",
            f"./server/audio/{track.id}.mp3",
        )
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.communicate()
        fetching_in_progress[track.id].set()

        try:
            return self.create_audio_url(track.id)
        except AudioNotFound:
            return

    async def queue(self, channel_id: int) -> List[str]:
        """This function is a coroutine

        Get the music queue of a voice channel.

        Parameters
        -----
        channel_id: ``int``
            The voice channel ID to get the music queue.

        Returns
        -----
        List[``str``]
            The list of IDs of tracks in the voice channel,
            this list can be empty.
        """
        row = await self.pool.fetchrow(f"SELECT * FROM youtube WHERE id = '{channel_id}';")
        if not row:
            await self.pool.execute(f"INSERT INTO youtube VALUES ('{channel_id}', $1);", [])
            track_ids = []
        else:
            track_ids = row["queue"]
        return track_ids

    async def add(self, channel_id: int, id: str) -> None:
        """This function is a coroutine

        Add a track to the music queue of a voice channel.

        Parameters
        -----
        channel_id: ``int``
            The voice channel ID.
        id: ``str``
            The ID of the track to add, in this case, a YouTube video
        """
        await self.pool.execute(f"UPDATE youtube SET queue = array_append(queue, '{id}') WHERE id = '{channel_id}';")

    async def remove(self, channel_id: int, *, pos: Optional[int] = None) -> Optional[str]:
        """This function is a coroutine

        Remove a track from the music queue of a voice channel.

        Parameters
        -----
        channel_id: ``int``
            The voice channel ID.
        pos: Optional[``int``]
            The position of the track to remove, indexing starts from 1. If
            this argument is not provided, a random track will be poped out.

        Returns
        -----
        Optional[``str``]
            The ID of the removed track, or ``None`` if the operation failed
        """
        queue = await self.queue(channel_id)
        pos = pos or random.randint(1, len(queue))
        try:
            track_id = queue[pos - 1]
            if pos < 1:
                raise IndexError
        except IndexError:
            pass
        else:
            await self.pool.execute(f"UPDATE youtube SET queue = array_cat(queue[:{pos - 1}], queue[{pos + 1}:]) WHERE id = '{channel_id}';")
            return track_id

    async def search(self, query: str, *, max_results: int = 6) -> List[PartialInvidiousSource]:
        """This function is a coroutine

        Search for a list of Invidious video from a query.

        Parameters
        -----
        query: ``str``
            The searching query
        max_results: ``int``
            The maximum number of results to return

        Returns
        -----
        List[``PartialInvidiousSource``]
            The list of searching results
        """
        return await PartialInvidiousSource.search(query, max_results=max_results, client=self)

    async def build(self, cls: Type[SourceT], track_id: str) -> Optional[SourceT]:
        """This function is a coroutine

        Build a ``PartialInvidiousSource`` or a ``InvidiousSource`` from a track ID.

        Parameters
        -----
        cls: Union[Type[``PartialInvidiousSource``], Type[``InvidiousSource``]]
            The object class to obtain.
        track_id: ``str``
            The track ID.

        Returns
        -----
        Optional[Union[``PartialInvidiousSource``, ``InvidiousSource``]]
            The track with the given ID, or ``None`` if not found.
        """
        return await cls.build(track_id, client=self)
