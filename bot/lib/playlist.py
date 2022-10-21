from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

import aiohttp
import asyncpg
import discord
from discord.utils import escape_markdown as escape

from lib.utils import slice_string
from lib.audio import constants, sources


class YouTubeCollectionBase:

    if TYPE_CHECKING:
        title: str
        id: str
        url: str
        videos: List[sources.PartialInvidiousSource]

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=slice_string(escape(self.title), 200),
            url=self.url,
        )

        added_count = 0
        for index, video in enumerate(self.videos):
            if not video.title or not video.channel:
                continue

            if added_count == 5:
                break

            embed.add_field(
                name=f"#{index + 1} {escape(video.title)}",
                value=escape(video.channel),
                inline=False,
            )

            added_count += 1

        return embed

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title={self.title} id={self.id}>"

    async def load(self, channel_id: int, *, conn: Union[asyncpg.Connection, asyncpg.Pool]) -> None:
        """This function is a coroutine

        Load this playlist to a voice channel's queue.

        Parameters
        -----
        channel_id: ``int``
            The voice channel ID.
        conn: Union[``asyncpg.Connection`, ``asyncpg.Pool``]
            The database connection or connection pool.
        """
        track_ids = [video.id for video in self.videos]
        await conn.execute(f"DELETE FROM youtube WHERE id = '{channel_id}';")
        await conn.execute(f"INSERT INTO youtube VALUES ('{channel_id}', $1);", track_ids)


class YouTubePlaylist(YouTubeCollectionBase):
    """Represents a playlist from YouTube."""

    __slots__ = ("title", "id", "author", "thumbnail", "description", "videos", "view", "url")
    if TYPE_CHECKING:
        title: str
        id: str
        author: str
        description: Optional[str]
        view: int
        videos: List[sources.PartialInvidiousSource]
        thumbnail: str
        url: str

    def __init__(self, data: Dict[str, Any], source_api: str) -> None:
        self.title = data["title"]
        self.id = data["playlistId"]
        self.author = data["author"]
        self.description = data.get("description")
        self.view = data["viewCount"]
        self.videos = [sources.PartialInvidiousSource(d, source_api) for d in data["videos"]]
        self.thumbnail = data["authorThumbnails"].pop()["url"]
        self.url = f"https://www.youtube.com/playlist?list={self.id}"

    def create_embed(self) -> discord.Embed:
        embed = super().create_embed()
        embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(
            name="Author",
            value=escape(self.author),
        )
        embed.add_field(
            name="Songs count",
            value=len(self.videos),
        )
        embed.add_field(
            name="View count",
            value=self.view,
        )

        return embed


class YouTubeMix(YouTubeCollectionBase):
    """Represents a playlist from YouTube."""

    __slots__ = ("title", "id", "videos", "url")
    if TYPE_CHECKING:
        title: str
        id: str
        videos: List[sources.PartialInvidiousSource]
        url: str

    def __init__(self, data: Dict[str, Any], source_api: str) -> None:
        self.title = data["title"]
        self.id = data["mixId"]
        self.videos = [sources.PartialInvidiousSource(d, source_api) for d in data["videos"]]
        self.url = f"https://www.youtube.com/playlist?list={self.id}"  # TODO: Find the appropriate URL format


async def get(id: str, *, session: aiohttp.ClientSession) -> Optional[Union[YouTubePlaylist, YouTubeMix]]:
    """This function is a coroutine

    Get a ``YouTubePlaylist` or ``YouTubeMix`` with
    the given ID.

    Parameters
    -----
    id: ``str``
        The playlist or mix ID.
    session: ``aiohttp.ClientSession``
        The session to perform the request

    Returns
    -----
    Optional[Union[``YouTubePlaylist``, ``YouTubeMix``]]
        The playlist or mix with the given ID, or
        ``None`` if not found.
    """
    for url in constants.INVIDIOUS_URLS:
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            # This endpoint can return either a playlist or a mix
            async with session.get(f"{url}/api/v1/playlists/{id}", timeout=constants.TIMEOUT) as response:
                if response.ok:
                    data = await response.json(encoding="utf-8")

                    # Cache all tracks, though their descriptions are unavailable
                    for d in data["videos"]:
                        await asyncio.to_thread(sources.save_to_memory, d)

                    cls = YouTubePlaylist if "playlistId" in data else YouTubeMix
                    return cls(data, url)
