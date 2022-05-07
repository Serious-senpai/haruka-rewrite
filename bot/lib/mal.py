from __future__ import annotations

import contextlib
from typing import (
    overload,
    Generic,
    Literal,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    TYPE_CHECKING,
)

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup as bs
from discord.utils import escape_markdown as escape

from lib import utils


T = TypeVar("T")
NSFW_ANIME_GENRES = set(["Ecchi", "Erotica", "Hentai"])
NSFW_MANGA_GENRES = set(["Ecchi", "Erotica", "Hentai"])
# References:
# https://myanimelist.net/anime.php
# https://myanimelist.net/manga.php


class MAL:
    """Base class for all MAL objects."""

    __slots__ = ("_soup",)
    if TYPE_CHECKING:
        _soup: bs4.BeautifulSoup

    def __init__(self, soup: bs4.BeautifulSoup) -> None:
        self._soup = soup

    @property
    def soup(self) -> bs4.BeautifulSoup:
        return self._soup


class MALObject(MAL, Generic[T]):
    """Represents an anime, manga,... from MyAnimeList."""

    __slots__ = ("id", "url", "title", "image_url", "score", "ranked", "popularity", "synopsis", "genres")
    if TYPE_CHECKING:
        id: int
        url: str
        title: str
        image_url: Optional[str]
        score: Optional[float]
        ranked: Optional[int]
        popularity: Optional[int]
        synopsis: Optional[str]
        genres: List[str]

    def __init__(self, id: Union[int, str], soup: bs4.BeautifulSoup) -> None:
        super().__init__(soup)
        self.id = int(id)
        self.url = f"https://myanimelist.net/{self.__class__.__name__.lower()}/{self.id}"
        self.title = self.soup.find(name="meta", attrs={"property": "og:title"}).get("content")

        try:
            self.image_url = self.soup.find(name="img", attrs={"itemprop": "image"}).get("data-src")
        except AttributeError:
            self.image_url = None

        try:
            _obj = self.soup.find(name="span", attrs={"itemprop": "ratingValue"}).get_text()
            self.score = float(_obj)
        except (AttributeError, ValueError):
            self.score = None

        try:
            _obj = self.soup.find(name="span", attrs={"itemprop": "ratingCount"}).get_text()
            self.ranked = int(_obj)
        except (AttributeError, ValueError):
            self.ranked = None

        try:
            _obj = self.soup.find(name="span", attrs={"class": "numbers popularity"}).strong.extract().get_text()[1:]
            self.popularity = int(_obj)
        except (AttributeError, ValueError):
            self.popularity = None

        try:
            self.synopsis = self.soup.find(name="meta", attrs={"property": "og:description"}).get("content")
        except AttributeError:
            self.synopsis = None

        __genres = self.soup.find_all(name="span", attrs={"itemprop": "genre"})
        self.genres = [genre.get_text() for genre in __genres]

    @overload
    def _data(self, category: str, cls: Type[T]) -> Optional[T]:
        ...

    @overload
    def _data(self, category: str) -> Optional[str]:
        ...

    def _data(self, category, cls=str):
        with contextlib.suppress(AttributeError, ValueError):
            obj = self.soup.find(
                name="span",
                string=category,
            ).parent
            obj.span.extract()
            return cls(obj.get_text(strip=True))

    def is_safe(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title={self.title} id={self.id} score={self.score} popularity={self.popularity}>"

    def create_embed(self) -> discord.Embed:
        title = escape(self.title)
        if self.synopsis:
            description = escape(self.synopsis)
        else:
            description = None

        embed = discord.Embed(
            title=utils.slice_string(title, 200),
            description=utils.slice_string(description, 4000),
            url=self.url,
        )
        return embed


class MALSearchResult(MAL):
    """Represents a search result from MyAnimeList.

    Note that it can be anything: anime, manga,...
    """

    __slots__ = ()

    @property
    def id(self) -> int:
        return int(self.url.split("/")[4])

    @property
    def url(self) -> str:
        return self.soup.get("href")

    @property
    def title(self) -> str:
        return self.soup.get_text()

    @classmethod
    async def search(
        cls: Type[MALSearchResult],
        query: str,
        *,
        criteria: Literal["manga", "anime"],
        session: aiohttp.ClientSession
    ) -> List[MALSearchResult]:
        rslt = []
        url = f"https://myanimelist.net/{criteria}.php"

        async with session.get(url, params={"q": query}) as response:
            if response.status == 200:
                html = await response.text(encoding="utf-8")
                soup = bs(html, "html.parser")
                obj = soup.find_all(
                    name="td",
                    attrs={"class": "borderClass bgColor0"},
                    limit=12,
                )
                for tag in enumerate(obj):
                    if tag[0] % 2 == 0:
                        continue
                    rslt.append(cls(tag[1].find("a")))

        return rslt


class Anime(MALObject):
    """Represents an anime from MyAnimeList."""

    __slots__ = ()

    @classmethod
    async def get(cls: Type[Anime], id: Union[int, str], *, session: aiohttp.ClientSession) -> Anime:
        url = f"https://myanimelist.net/anime/{id}"
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text(encoding="utf-8")
            soup = bs(html, "html.parser")
            return cls(id, soup)

    def is_safe(self) -> bool:
        for genre in self.genres:
            if genre in NSFW_ANIME_GENRES:
                return False

        return True

    def create_embed(self) -> discord.Embed:
        embed = super().create_embed()
        embed.set_thumbnail(url=self.image_url)
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
            value=self._data("Aired:"),
        )
        embed.add_field(
            name="Status",
            value=self._data("Status:"),
        )
        embed.add_field(
            name="Ranked",
            value=f"#{self.ranked}",
        )
        embed.add_field(
            name="Popularity",
            value=f"#{self.popularity}",
        )
        embed.add_field(
            name="Episodes",
            value=self._data("Episodes:", int),
        )
        embed.add_field(
            name="Type",
            value=self._data("Type:"),
        )
        embed.add_field(
            name="Broadcast",
            value=self._data("Broadcast:"),
        )
        embed.add_field(
            name="Link reference",
            value=f"[MyAnimeList link]({self.url})",
            inline=False,
        )
        return embed


class Manga(MALObject):
    """Represents a manga from MyAnimeList."""

    __slots__ = ()

    @classmethod
    async def get(cls: Type[Manga], id: Union[int, str], *, session: aiohttp.ClientSession) -> Manga:
        url = f"https://myanimelist.net/manga/{id}"
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text(encoding="utf-8")
            soup = bs(html, "html.parser")
            return cls(id, soup)

    def is_safe(self) -> bool:
        for genre in self.genres:
            if genre in NSFW_MANGA_GENRES:
                return False

        return True

    def create_embed(self) -> discord.Embed:
        embed = super().create_embed()
        embed.set_thumbnail(url=self.image_url)
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
            value=self._data("Published:")
        )
        embed.add_field(
            name="Ranked",
            value=f"#{self.ranked}",
        )
        embed.add_field(
            name="Popularity",
            value=f"#{self.popularity}",
        )
        embed.add_field(
            name="Episodes",
            value=self._data("Episodes:", int),
        )
        embed.add_field(
            name="Chapters",
            value=self._data("Chapters:", int),
        )
        embed.add_field(
            name="Type",
            value=self._data("Type:"),
        )
        embed.add_field(
            name="Link reference",
            value=f"[MyAnimeList link]({self.url})",
            inline=False,
        )
        return embed
