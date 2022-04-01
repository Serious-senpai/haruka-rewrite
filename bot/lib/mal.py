from __future__ import annotations

import contextlib
from typing import Generic, Literal, List, Optional, Type, TypeVar, Union, TYPE_CHECKING

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup as bs
from discord.utils import escape_markdown as escape


T = TypeVar("T")


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

    def __init__(self, id: int, soup: bs4.BeautifulSoup) -> None:
        super().__init__(soup)
        self.id = id
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

    def data(self, category: str, cls: Type[T] = str) -> Optional[T]:
        with contextlib.suppress(AttributeError, ValueError):
            obj = self.soup.find(
                name="span",
                string=category,
            ).parent
            obj.span.extract()
            return cls(obj.get_text(strip=True))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title={self.title} id={self.id} score={self.score} popularity={self.popularity}>"

    def create_embed(self) -> discord.Embed:
        title = escape(self.title)
        if self.synopsis:
            description = escape(self.synopsis)
            if len(description) > 4000:
                description = description[:4000] + f" [...]({self.url})"

        embed = discord.Embed(title=title, description=description, url=self.url)
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
        criteria: Literal["manga, anime"],
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
            if response.ok:
                html = await response.text(encoding="utf-8")
                soup = bs(html, "html.parser")
                return cls(id, soup)
            else:
                return

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
            value=self.data("Aired:"),
        )
        embed.add_field(
            name="Status",
            value=self.data("Status:"),
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
            value=self.data("Episodes:", int),
        )
        embed.add_field(
            name="Type",
            value=self.data("Type:"),
        )
        embed.add_field(
            name="Broadcast",
            value=self.data("Broadcast:"),
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
    async def get(cls: Type[Manga], id: int, *, session: aiohttp.ClientSession) -> Manga:
        url = f"https://myanimelist.net/manga/{id}"
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text(encoding="utf-8")
                soup = bs(html, "html.parser")
                return cls(id, soup)
            else:
                return

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
            value=self.data("Published:")
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
            value=self.data("Episodes:", int),
        )
        embed.add_field(
            name="Chapters",
            value=self.data("Chapters:", int),
        )
        embed.add_field(
            name="Type",
            value=self.data("Type:"),
        )
        embed.add_field(
            name="Link reference",
            value=f"[MyAnimeList link]({self.url})",
            inline=False,
        )
        return embed
