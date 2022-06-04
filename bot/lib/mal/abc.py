from __future__ import annotations

import contextlib
from typing import Generic, List, Optional, Type, TypeVar, Union, overload, TYPE_CHECKING

import bs4
import discord
from discord.utils import escape_markdown as escape

from lib import utils

__all__ = ("MALObject",)
T = TypeVar("T")


class MALObject:
    """Represents an anime, manga,... from MyAnimeList."""

    __slots__ = ("soup", "id", "url", "title", "image_url", "score", "ranked", "popularity", "synopsis", "genres")
    if TYPE_CHECKING:
        soup: bs4.BeautifulSoup
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
        self.soup = soup
        self.id = int(id)
        self.url = f"https://myanimelist.net/{self.__class__.__name__.lower()}/{self.id}"
        self.title = self.soup.find(name="meta", attrs={"property": "og:title"}).get("content")

        try:
            self.image_url = self.soup.find(name="meta", attrs={"property": "og:image"}).get("content")
        except AttributeError:
            self.image_url = None

        try:
            _obj = self.soup.find(name="span", attrs={"itemprop": "ratingValue"}).get_text()
            self.score = float(_obj)
        except (AttributeError, ValueError):
            self.score = None

        try:
            _obj = self.soup.find(name="span", attrs={"class": "numbers ranked"}).strong.extract().get_text().removeprefix("#")
            self.ranked = int(_obj)
        except (AttributeError, ValueError):
            self.ranked = None

        try:
            _obj = self.soup.find(name="span", attrs={"class": "numbers popularity"}).strong.extract().get_text().removeprefix("#")
            self.popularity = int(_obj)
        except (AttributeError, ValueError):
            self.popularity = None

        try:
            self.synopsis = self.soup.find(name="meta", attrs={"property": "og:description"}).get("content")
        except AttributeError:
            self.synopsis = None

        _genres = self.soup.find_all(name="span", attrs={"itemprop": "genre"})
        self.genres = [genre.get_text() for genre in _genres]

        self.__postinit__()

    def __postinit__(self) -> None:
        return

    @overload
    def extract_span(self, category: str, cls: Type[T]) -> Optional[T]:
        ...

    @overload
    def extract_span(self, category: str) -> Optional[str]:
        ...

    def extract_span(self, category, cls=str):
        with contextlib.suppress(AttributeError, ValueError):
            obj = self.soup.find(name="span", string=category).parent
            obj.span.extract()
            return cls(obj.get_text(strip=True))

    def is_safe(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title={self.title} id={self.id} score={self.score} ranked={self.ranked} popularity={self.popularity}>"

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
