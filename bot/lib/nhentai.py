from __future__ import annotations

import contextlib
import re
from typing import List, Optional, Type, Union, TYPE_CHECKING

import aiohttp
import bs4
import discord
from discord.utils import escape_markdown as escape


ID_PATTERN = re.compile(r"(?<!\d)\d{6}(?!\d)")


class NHentaiSearch:
    """Represents a search result from nhentai.net"""

    __slots__ = ("title", "thumbnail", "path", "id")
    if TYPE_CHECKING:
        title: str
        thumbnail: Optional[str]
        path: str
        id: int

    def __init__(self, soup: bs4.BeautifulSoup) -> None:
        self.title = soup.find("div", attrs={"class": "caption"}).get_text()
        with contextlib.suppress(AttributeError):
            self.thumbnail = soup.find("img").get("data-src")

        self.path = soup.find("a").get("href")
        self.id = int(self.path.split("/")[2])

    @property
    def thumb(self) -> Optional[str]:
        return self.thumbnail

    def __repr__(self) -> str:
        return f"<NHentaiSearch title={self.title} id={self.id}>"

    @classmethod
    async def search(cls: Type[NHentaiSearch], query: str, *, session: aiohttp.ClientSession) -> List[NHentaiSearch]:
        """This function is a coroutine

        Search for a list of doujinshis from a query. The number of
        results is not predictable so it is recommended to slice the
        returned list to get only the first 6 results for most use
        cases.

        Parameters
        -----
        query: ``str``
            The searching query

        Returns
        -----
        List[``NHentaiSearch``]
            The list of search results. If no result was found then an
            empty list is returned
        """
        async with session.get("https://nhentai.net/search/", params={"q": query}) as response:
            if response.ok:
                html = await response.text(encoding="utf-8")
                soup = bs4.BeautifulSoup(html, "html.parser")
                container = soup.find("div", attrs={"class": "container index-container"})
                # Even when no result is found and the page
                # displays 404, the response status is still
                # 200 so another check is necessary.
                if not container:
                    return
                doujins = container.find_all("div", attrs={"class": "gallery"})
                return list(cls(doujin) for doujin in doujins)

        return []


class NHentai:
    """Represents a doujinshi from nhentai.net"""

    __slots__ = ("id", "title", "url", "sections", "thumbnail", "subtitle")
    if TYPE_CHECKING:
        id: int
        title: str
        url: str
        sections: bs4.element.ResultSet[bs4.Tag]
        thumbnail: Optional[str]
        subtitle: Optional[str]

    def __init__(self, soup: bs4.BeautifulSoup):
        _container = soup.find("div", attrs={"class": "container"})
        self.id = int(_container.find("a").get("href").split("/")[2])
        self.title = _container.find("h1", attrs={"class": "title"}).find("span", attrs={"class": "pretty"}).get_text()
        self.url = f"https://nhentai.net/g/{self.id}"
        self.sections = _container.find("section", attrs={"id": "tags"}).find_all("div")

        try:
            self.thumbnail = _container.find("img").get("data-src")
        except AttributeError:
            self.thumbnail = None

        try:
            self.subtitle = _container.find("h2", attrs={"class": "title"}).find("span", attrs={"class": "pretty"}).get_text()
        except AttributeError:
            self.subtitle = None

    @property
    def thumb(self) -> Optional[str]:
        return self.thumbnail

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.subtitle) if self.subtitle else None,
            url=self.url,
        )
        for section in self.sections:
            span = section.span.extract()
            content = span.find_all("a")

            if not content:
                continue

            name = section.get_text().strip().replace(":", "")
            embed.add_field(
                name=name,
                value=", ".join(
                    obj.find("span", attrs={"class": "name"}).get_text() for obj in content
                ),
                inline=name not in ("Characters", "Tags"),
            )

        embed.add_field(
            name="Link",
            value=self.url,
            inline=False,
        )
        embed.set_thumbnail(url=self.thumbnail)
        return embed

    def __repr__(self) -> str:
        return f"<NHentai title={self.title} id={self.id}>"

    @classmethod
    async def get(cls: Type[NHentai], id: Union[int, str], *, session: aiohttp.ClientSession) -> Optional[NHentai]:
        """This function is a coroutine

        Get a NHentai doujinshi from an ID

        Parameters
        -----
        id: Union[``int``, ``str``]
            The doujinshi ID

        Returns
        -----
        Optional[``NHentai``]
            The doujinshi with the given ID, or ``None`` if an invalid
            ID was passed, or any HTTP errors occured (4xx or 5xx
            status)
        """
        async with session.get(f"https://nhentai.net/g/{id}") as response:
            if response.ok:
                html = await response.text(encoding="utf-8")
                soup = bs4.BeautifulSoup(html, "html.parser")
                return cls(soup)
