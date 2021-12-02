from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Type, Union

import asyncpg
import discord
from discord.utils import escape_markdown as escape

import audio
import haruka


class Playlist:
    """Represents a music playlist constructed from
    a database row.

    This object should never be created manually, use
    its classmethods instead.

    Attributes
    -----
    id: :class:`int`
        The playlist ID.
    title: :class:`str`
        The title of the playlist.
    description: :class:`str`
        The description of the playlist.
    author: :class:`discord.User`
        The author of the playlist.
    queue: List[:class:`str`]
        List of track IDs this playlist has.
    """

    __slots__ = (
        "id",
        "title",
        "description",
        "queue",
        "use_count",
        "author",
    )

    def __init__(self, row: asyncpg.Record, author: Optional[discord.User]) -> None:
        self.id: int = row["id"]
        self.title: str = row["title"]
        self.description: str = row["description"]
        self.queue: List[str] = row["queue"]
        self.use_count: int = row["use_count"]
        self.author: Optional[discord.User] = author

    def create_embed(self) -> discord.Embed:
        """Create an embed for this playlist."""
        embed: discord.Embed = discord.Embed(
            title = self.title,
            description = self.description,
            color = 0x2ECC71,
        )

        if self.author:
            embed.set_thumbnail(url = self.author.avatar.url if self.author.avatar else discord.Embed.Empty)

        embed.add_field(
            name = "Playlist ID",
            value = self.id,
            inline = False,
        )
        embed.add_field(
            name = "Author",
            value = escape(str(self.author)),
        )
        embed.add_field(
            name = "Tracks count",
            value = len(self.queue),
        )
        embed.add_field(
            name = "Usage count",
            value = self.use_count,
        )
        return embed

    @classmethod
    async def search(cls: Type[Playlist], bot: haruka.Haruka, query: str) -> List[Playlist]:
        """This function is a coroutine

        Search for a maximum of 6 playlists whose names match
        the searching query.

        Parameters
        -----
        bot: :class:`haruka.Haruka`
            The bot that initialized the request.
        query :class:`str`
            The searching query.

        Returns
        -----
        List[:class:`Playlist`]
            A list of results, this may be empty.
        """
        rows: List[asyncpg.Record] = await bot.conn.fetch(f"""
            SELECT *
            FROM playlist
            WHERE similarity(title, '{query}') > 0.35
            ORDER BY similarity(title, '{query}')
            LIMIT 6;
        """)
        results: List[Playlist] = []
        cached: Dict[int, Optional[discord.User]] = {}
        for row in rows:
            author_id: int = int(row["author_id"])

            author: Optional[discord.User]
            if author_id in cached:
                author = cached[author_id]

            else:
                try:
                    author = await bot.fetch_user(author_id)
                except:
                    author = None

                cached[author_id] = author

            results.append(cls(row, author))

        return results

    @classmethod
    async def get(cls: Type[Playlist], bot: haruka.Haruka, id: int) -> Optional[Playlist]:
        """This function is a coroutine

        Get a playlist from the given ID.

        Parameters
        -----
        bot: :class:`haruka.Haruka`
            The bot that initialized the request.
        id :class:`int`
            The playlist ID

        Returns
        -----
        Optional[:class:`Playlist`]
            The playlist with the given ID, or ``None`` if not found.
        """
        row: Optional[asyncpg.Record] = await bot.conn.fetchrow("SELECT * FROM playlist WHERE id = $1", id)

        if row:
            author_id: int = int(row["author_id"])
            author: Optional[discord.User]

            try:
                author = await bot.fetch_user(author_id)
            except:
                author = None

            return cls(row, author)


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
            title = escape(self.title),
            description = escape(self.description),
            color = 0x2ECC71,
        )
        embed.set_thumbnail(url = self.thumbnail)
        embed.add_field(
            name = "Author",
            value = escape(self.author),
        )
        embed.add_field(
            name = "Songs count",
            value = len(self.videos),
        )
        embed.add_field(
            name = "View count",
            value = self.view,
        )
        for index, video in enumerate(self.videos[:5]):
            embed.add_field(
                name = f"#{index + 1} {escape(video['title'])}",
                value = escape(video["author"]),
                inline = False,
            )
        return embed

    async def load(self, conn: Union[asyncpg.Connection, asyncpg.Pool], channel_id: int) -> None:
        """This function is a coroutine

        Load this playlist to a voice channel's queue.

        Parameters
        -----
        conn: Union[:class:`asyncpg.Connection`, :class:`asyncpg.Pool`]
            The database connection or connection pool.
        channel_id: :class:`int`
            The voice channel ID.
        """
        track_ids: List[str] = [video["videoId"] for video in self.videos]
        await conn.execute(f"DELETE FROM youtube WHERE id = '{channel_id}';")
        await conn.execute(f"INSERT INTO youtube VALUES ('{channel_id}', $1);", track_ids)

    @classmethod
    async def get(cls: Type[YouTubePlaylist], bot: haruka.Haruka, id: str) -> Optional[YouTubePlaylist]:
        """This function is a coroutine

        Get a :class:`YouTubePlaylist` with the given ID.

        Parameters
        -----
        bot: :class:`haruka.Haruka`
            The bot that initialized the request.
        id: :class:`str`
            The playlist ID.
        
        Returns
        -----
        Optional[:class:`YouTubePlaylist`]
            The playlist with the given ID, or ``None``
            if not found.
        """
        for url in audio.INVIDIOUS_URLS:
            async with bot.session.get(f"{url}/api/v1/playlists/{id}", timeout = audio.TIMEOUT) as response:
                if response.ok:
                    data: Dict[str, Any] = await response.json()

                    # Cache all tracks, though their descriptions are unavailable
                    video: Dict[str, Any]
                    for video in data["videos"]:
                        video["api_url"] = url
                        await asyncio.to_thread(audio.save_to_memory, video)

                    return cls(data)
