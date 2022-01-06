from __future__ import annotations

import contextlib
from typing import Dict, Generic, Literal, List, Optional, Type, TypeVar, Union

import bs4
import discord
from bs4 import BeautifulSoup as bs
from discord.utils import escape_markdown as escape

from core import bot


T = TypeVar("T")


class MAL:
    """Base class for all MAL objects."""

    __slots__ = (
        "_soup",
    )

    def __init__(self, soup: bs4.BeautifulSoup) -> None:
        self._soup: bs4.BeautifulSoup = soup

    @property
    def soup(self) -> bs4.BeautifulSoup:
        return self._soup


class MALObject(MAL, Generic[T]):
    """Represents an anime, manga,... from MyAnimeList."""

    __slots__ = (
        "_id",
        "_soup",
    )

    def __init__(self, id: int, soup: bs4.BeautifulSoup) -> None:
        self._id: int = id
        self._soup: bs4.BeautifulSoup = soup

    @property
    def id(self) -> int:
        return self._id

    @property
    def url(self) -> str:
        return f"https://myanimelist.net/{self.__class__.__name__.lower()}/{self.id}"

    @property
    def title(self) -> str:
        return self.soup.find(name="meta", attrs={"property": "og:title"}).get("content")

    @property
    def image_url(self) -> Union[str, discord.embeds._EmptyEmbed]:
        try:
            return self.soup.find(name="img", attrs={"itemprop": "image"}).get("data-src")
        except AttributeError:
            return discord.Embed.Empty

    @property
    def score(self) -> Optional[float]:
        with contextlib.suppress(AttributeError, ValueError):
            obj: str = self.soup.find(name="span", attrs={"itemprop": "ratingValue"}).get_text()
            return float(obj)

    @property
    def ranked(self) -> Optional[int]:
        with contextlib.suppress(AttributeError, ValueError):
            obj: str = self.soup.find(name="span", attrs={"itemprop": "ratingCount"}).get_text()
            return int(obj)

    @property
    def popularity(self) -> Optional[int]:
        with contextlib.suppress(AttributeError, ValueError):
            obj: str = self.soup.find(name="span", attrs={"class": "numbers popularity"}).strong.extract().get_text()[1:]
            return int(obj)

    @property
    def genres(self) -> List[str]:
        genres_ = self.soup.find_all(name="span", attrs={"itemprop": "genre"})
        return [genre.get_text() for genre in genres_]

    @property
    def synopsis(self) -> Optional[str]:
        with contextlib.suppress(AttributeError):
            return self.soup.find(name="meta", attrs={"property": "og:description"}).get("content")

    def data(self, category: str, cls: Type[T] = str) -> Optional[T]:
        with contextlib.suppress(AttributeError, ValueError):
            obj: bs4.BeautifulSoup = self.soup.find(
                name="span",
                string=category,
            ).parent
            _ = obj.span.extract()
            return cls(obj.get_text(strip=True))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title={self.title} id={self.id} score={self.score} popularity={self.popularity}>"


class MALSearchResult(MAL):
    """Represents a search result from MyAnimeList.

    Note that it can be anything: anime, manga,...
    """

    __slots__ = (
        "_soup",
    )

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
    ) -> List[MALSearchResult]:
        rslt: List[MALSearchResult] = []
        params: Dict[str, str] = {
            "q": query,
        }
        url = f"https://myanimelist.net/{criteria}.php"

        async with bot.session.get(url, params=params) as response:
            if response.status == 200:
                html: str = await response.text(encoding="utf-8")
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

    __slots__ = (
        "_id",
        "_soup",
    )

    @classmethod
    async def get(cls: Type[Anime], id: Union[int, str]) -> Anime:
        url = f"https://myanimelist.net/anime/{id}"
        async with bot.session.get(url) as response:
            if response.ok:
                html: str = await response.text(encoding="utf-8")
                soup = bs(html, "html.parser")
                return cls(id, soup)
            else:
                return

    def create_embed(self) -> discord.Embed:
        em: discord.Embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.synopsis[:4096]),
        )
        em.set_thumbnail(url=self.image_url)
        em.add_field(
            name="Genres",
            value=", ".join(self.genres),
            inline=False,
        )
        em.add_field(
            name="Score",
            value=self.score,
            inline=False,
        )
        em.add_field(
            name="Aired",
            value=self.data("Aired:"),
        )
        em.add_field(
            name="Status",
            value=self.data("Status:"),
        )
        em.add_field(
            name="Ranked",
            value=f"#{self.ranked}",
        )
        em.add_field(
            name="Popularity",
            value=f"#{self.popularity}",
        )
        em.add_field(
            name="Episodes",
            value=self.data("Episodes:", int),
        )
        em.add_field(
            name="Type",
            value=self.data("Type:"),
        )
        em.add_field(
            name="Broadcast",
            value=self.data("Broadcast:"),
        )
        em.add_field(
            name="Link reference",
            value=f"[MyAnimeList link]({self.url})",
            inline=False,
        )
        return em


class Manga(MALObject):
    """Represents a manga from MyAnimeList."""

    __slots__ = (
        "_id",
        "_soup",
    )

    @classmethod
    async def get(cls: Type[Manga], id: int) -> Manga:
        url = f"https://myanimelist.net/manga/{id}"
        async with bot.session.get(url) as response:
            if response.status == 200:
                html: str = await response.text(encoding="utf-8")
                soup = bs(html, "html.parser")
                return cls(id, soup)
            else:
                return

    def create_embed(self) -> discord.Embed:
        em: discord.Embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.synopsis[:4096]),
        )
        em.set_thumbnail(url=self.image_url)
        em.add_field(
            name="Genres",
            value=", ".join(self.genres),
            inline=False,
        )
        em.add_field(
            name="Score",
            value=self.score,
            inline=False,
        )
        em.add_field(
            name="Published",
            value=self.data("Published:")
        )
        em.add_field(
            name="Ranked",
            value=f"#{self.ranked}",
        )
        em.add_field(
            name="Popularity",
            value=f"#{self.popularity}",
        )
        em.add_field(
            name="Episodes",
            value=self.data("Episodes:", int),
        )
        em.add_field(
            name="Chapters",
            value=self.data("Chapters:", int),
        )
        em.add_field(
            name="Type",
            value=self.data("Type:"),
        )
        em.add_field(
            name="Link reference",
            value=f"[MyAnimeList link]({self.url})",
            inline=False,
        )
        return em
