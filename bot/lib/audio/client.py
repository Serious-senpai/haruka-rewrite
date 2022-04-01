from __future__ import annotations

import asyncio
import os
import random
from typing import Dict, Callable, List, Optional, Type, TypeVar, TYPE_CHECKING

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from env import HOST
from .exceptions import AudioNotFound
from .sources import PartialInvidiousSource, InvidiousSource
if TYPE_CHECKING:
    import haruka
    from _types import Context


__all__ = ("AudioClient",)


fetching_in_progress: Dict[str, asyncio.Event] = {}
if TYPE_CHECKING:
    T = TypeVar("T")
    SourceT = TypeVar("SourceT", PartialInvidiousSource, InvidiousSource)


class AudioClient:

    __slots__ = ("bot", "pool", "session")
    if TYPE_CHECKING:
        bot: haruka.Haruka
        pool: asyncpg.Pool
        session: aiohttp.ClientSession

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self.pool = bot.conn
        self.session = aiohttp.ClientSession

    def in_voice(self) -> Callable[[T], T]:
        """A text command check that returns ``True`` if the invoker is
        currently in a voice channel.
        """
        async def predicate(ctx: Context) -> bool:
            if not getattr(ctx.author, "voice", None):
                await ctx.send("Please join a voice channel first.")
                return False

            return True
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

    async def fetch(self, track: InvidiousSource) -> str:
        """This function is a coroutine

        Download a video audio to the local machine and return its URL.

        Parameters
        -----
        track: ``InvidiousSource``
            The target track.

        Returns
        -----
        ``str``
            The URL to the audio, remember that we are hosting
            on Heroku.

        Raises
        -----
        ``AudioNotFound``
            The downloading process failed somehow
        """
        try:
            await fetching_in_progress[track.id].wait()
            return self.create_audio_url(track.id)
        except KeyError:
            fetching_in_progress[track.id] = asyncio.Event()

        url = await track.ensure_source()
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
        return self.create_audio_url(track.id)

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
        await self.execute(f"UPDATE youtube SET queue = array_append(queue, '{id}') WHERE id = '{channel_id}';")

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
        return await cls.build(track_id, client=self)