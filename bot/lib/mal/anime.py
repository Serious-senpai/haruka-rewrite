from __future__ import annotations

from typing import Optional, Type, Union, TYPE_CHECKING

import aiohttp
import bs4
import discord

from .abc import MALObject
from .constants import NSFW_ANIME_GENRES


__all__ = ("Anime",)


class Anime(MALObject):
    """Represents an anime from MyAnimeList."""

    __slots__ = ("aired", "status", "episodes", "type", "broadcast")
    if TYPE_CHECKING:
        aired: Optional[str]
        status: Optional[str]
        episodes: Optional[int]
        type: Optional[str]
        broadcast: Optional[str]

    def __postinit__(self) -> None:
        self.aired = self.extract_span("Aired:")
        self.status = self.extract_span("Status:")
        self.episodes = self.extract_span("Episodes:", int)
        self.type = self.extract_span("Type:")
        self.broadcast = self.extract_span("Broadcast:")

    @classmethod
    async def get(cls: Type[Anime], id: Union[int, str], *, session: aiohttp.ClientSession) -> Anime:
        url = f"https://myanimelist.net/anime/{id}"
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text(encoding="utf-8")
            soup = bs4.BeautifulSoup(html, "html.parser")
            return cls(id, soup)

    def is_safe(self) -> bool:
        for genre in self.genres:
            if genre in NSFW_ANIME_GENRES:
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
            name="Aired",
            value=self.aired,
        )
        embed.add_field(
            name="Status",
            value=self.status,
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
            name="Type",
            value=self.type,
        )
        embed.add_field(
            name="Broadcast",
            value=self.broadcast,
        )
        embed.add_field(
            name="Link reference",
            value=f"[MyAnimeList link]({self.url})",
            inline=False,
        )
        return embed
