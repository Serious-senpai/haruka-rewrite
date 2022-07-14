from __future__ import annotations

from typing import Optional, Type, Union, TYPE_CHECKING

import aiohttp
import bs4
import discord

from .abc import MALObject
from .constants import NSFW_MANGA_GENRES


__all__ = ("Manga",)


class Manga(MALObject):
    """Represents a manga from MyAnimeList."""

    __slots__ = ("published", "episodes", "chapters", "type")
    if TYPE_CHECKING:
        published: Optional[str]
        episodes: Optional[int]
        chapters: Optional[int]
        type: Optional[str]

    def __postinit__(self) -> None:
        self.published = self.extract_span("Published:")
        self.episodes = self.extract_span("Episodes:", int)
        self.chapters = self.extract_span("Chapters:", int)
        self.type = self.extract_span("Type:")

    @classmethod
    async def get(cls: Type[Manga], id: Union[int, str], *, session: aiohttp.ClientSession) -> Manga:
        url = f"https://myanimelist.net/manga/{id}"
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text(encoding="utf-8")
            soup = bs4.BeautifulSoup(html, "html.parser")
            return cls(id, soup)

    def is_safe(self) -> bool:
        for genre in self.genres:
            if genre in NSFW_MANGA_GENRES:
                return False

        return True

    def create_embed(self) -> discord.Embed:
        embed = super().create_embed()
        embed.set_thumbnail(url=self.image_url)

        if self.genres:
            embed.add_field(
                name="Genres",
                value=", ".join(self.genres),
                inline=False,
            )

        embed.add_field(
            name="Score",
            value=self.score,
            inline=False,
        )
        embed.add_field(
            name="Published",
            value=self.published,
        )
        embed.add_field(
            name="Ranked",
            value=f"#{self.ranked}" if self.ranked else "*N/A*",
        )
        embed.add_field(
            name="Popularity",
            value=f"#{self.popularity}" if self.popularity else "*N/A*",
        )
        embed.add_field(
            name="Episodes",
            value=self.episodes,
        )
        embed.add_field(
            name="Chapters",
            value=self.chapters,
        )
        embed.add_field(
            name="Type",
            value=self.type,
        )
        embed.add_field(
            name="Link reference",
            value=f"[MyAnimeList link]({self.url})",
            inline=False,
        )
        return embed
