from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Dict, List, Optional, Type, Union

import aiohttp
import asyncpg
import discord
from discord.utils import escape_markdown as escape

import audio
import haruka


class YouTubePlaylist:
    """Represents a playlist from YouTube."""
    __slots__ = (
        "title",
        "id",
        "author",
        "thumbnail",
        "description",
        "videos",
        "view",
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        self.title: str = data["title"]
        self.id: str = data["playlistId"]
        self.author: str = data["author"]
        self.description: str = data.get("description", "No description")
        self.view: int = data["viewCount"]
        self.videos: List[Dict[str, Any]] = data["videos"]
        self.thumbnail: str = data["authorThumbnails"].pop()["url"]

    def create_embed(self) -> discord.Embed:
        embed: discord.Embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.description),
        )
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
        for index, video in enumerate(self.videos[:5]):
            embed.add_field(
                name=f"#{index + 1} {escape(video['title'])}",
                value=escape(video["author"]),
                inline=False,
            )
        return embed

    async def load(self, conn: Union[asyncpg.Connection, asyncpg.Pool], channel_id: int) -> None:
        """This function is a coroutine

        Load this playlist to a voice channel's queue.

        Parameters
        -----
        conn: Union[``asyncpg.Connection`, ``asyncpg.Pool``]
            The database connection or connection pool.
        channel_id: ``int``
            The voice channel ID.
        """
        track_ids: List[str] = [video["videoId"] for video in self.videos]
        await conn.execute(f"DELETE FROM youtube WHERE id = '{channel_id}';")
        await conn.execute(f"INSERT INTO youtube VALUES ('{channel_id}', $1);", track_ids)

    @classmethod
    async def get(cls: Type[YouTubePlaylist], bot: haruka.Haruka, id: str) -> Optional[YouTubePlaylist]:
        """This function is a coroutine

        Get a ``YouTubePlaylist`` with the given ID.

        Parameters
        -----
        bot: ``haruka.Haruka``
            The bot that initialized the request.
        id: ``str``
            The playlist ID.

        Returns
        -----
        Optional[``YouTubePlaylist``]
            The playlist with the given ID, or ``None``
            if not found.
        """
        for url in audio.INVIDIOUS_URLS:
            with contextlib.suppress(aiohttp.ClientError):
                async with bot.session.get(f"{url}/api/v1/playlists/{id}", timeout=audio.TIMEOUT) as response:
                    if response.ok:
                        data: Dict[str, Any] = await response.json()

                        # Cache all tracks, though their descriptions are unavailable
                        video: Dict[str, Any]
                        for video in data["videos"]:
                            video["api_url"] = url
                            await asyncio.to_thread(audio.save_to_memory, video)

                        return cls(data)
