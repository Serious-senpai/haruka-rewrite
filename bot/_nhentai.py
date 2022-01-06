from __future__ import annotations

import contextlib
import re
from typing import List, Optional, Type, Union

import bs4
import discord
from discord.utils import escape_markdown as escape

from core import bot


ID_PATTERN: re.Pattern = re.compile(r"^(?<!\d)\d{6,6}(?!\d)$")


class NHentaiSearch:
    """Represents a search result from nhentai.net"""

    __slots__ = (
        "_soup",
    )

    def __init__(self, soup: bs4.BeautifulSoup):
        self._soup: bs4.BeautifulSoup = soup

    @property
    def soup(self) -> bs4.BeautifulSoup:
        return self._soup

    @property
    def title(self) -> str:
        return self.soup.find("div", attrs={"class": "caption"}).get_text()

    @property
    def thumbnail(self) -> Optional[str]:
        with contextlib.suppress(AttributeError):
            return self.soup.find("img").get("data-src")

    @property
    def thumb(self) -> Optional[str]:
        return self.thumbnail

    @property
    def path(self) -> str:
        return self.soup.find("a").get("href")

    @property
    def id(self) -> int:
        return int(self.path.split("/")[2])

    def __repr__(self) -> str:
        return f"<NHentaiSearch title={self.title} id={self.id}>"

    @classmethod
    async def search(cls: Type[NHentaiSearch], query: str) -> List[NHentaiSearch]:
        """This function is a coroutine

        Search for a list of doujinshis from a query. The number of
        results is not predictable so it is recommended to slice the
        returnedclist to get only the first 6 results for most use
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
        params = {"q": query}
        async with bot.session.get("https://nhentai.net/search/", params=params) as response:
            if response.ok:
                html: str = await response.text(encoding="utf-8")
                soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
                container: bs4.BeautifulSoup = soup.find("div", attrs={"class": "container index-container"})
                # Even when no result is found and the page
                # displays 404, the response status is still
                # 200 so another check is necessary.
                if not container:
                    return
                doujins: bs4.element.ResultSet[bs4.BeautifulSoup] = container.find_all("div", attrs={"class": "gallery"})
                return list(cls(doujin) for doujin in doujins)

        return []


class NHentai:
    """Represents a doujinshi from nhentai.net"""

    __slots__ = (
        "_soup",
    )

    def __init__(self, soup: bs4.BeautifulSoup):
        self._soup: bs4.BeautifulSoup = soup.find("div", attrs={"class": "container"})

    @property
    def soup(self) -> bs4.BeautifulSoup:
        return self._soup

    @property
    def id(self) -> int:
        return int(self.soup.find("a").get("href").split("/")[2])

    @property
    def url(self) -> str:
        return f"https://nhentai.net/g/{self.id}"

    @property
    def thumbnail(self) -> Optional[str]:
        with contextlib.suppress(AttributeError):
            return self.soup.find("img").get("data-src")

    @property
    def thumb(self) -> Optional[str]:
        return self.thumbnail

    @property
    def title(self) -> str:
        return self.soup.find("h1", attrs={"class": "title"}).find("span", attrs={"class": "pretty"}).get_text()

    @property
    def subtitle(self) -> Optional[str]:
        with contextlib.suppress(AttributeError):
            return self.soup.find("h2", attrs={"class": "title"}).find("span", attrs={"class": "pretty"}).get_text()

    @property
    def sections(self) -> List[bs4.BeautifulSoup]:
        return self.soup.find("section", attrs={"id": "tags"}).find_all("div")

    def create_embed(self) -> discord.Embed:
        em: discord.Embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.subtitle) if self.subtitle else discord.Embed.Empty,
            url=self.url,
        )
        for section in self.sections:
            span: bs4.BeautifulSoup = section.span.extract()
            content: List[bs4.BeautifulSoup] = span.find_all("a")

            if not content:
                continue

            name: str = section.get_text().strip().replace(":", "")
            em.add_field(
                name=name,
                value=", ".join(
                    obj.find("span", attrs={"class": "name"}).get_text() for obj in content
                ),
                inline=name not in ("Characters", "Tags"),
            )

        em.add_field(
            name="Link",
            value=self.url,
            inline=False,
        )
        em.set_thumbnail(url=self.thumbnail or discord.Embed.Empty)
        return em

    def __repr__(self) -> str:
        return f"<NHentai title={self.title} id={self.id}>"

    @classmethod
    async def get(cls: Type[NHentai], id: Union[int, str]) -> Optional[NHentai]:
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
        async with bot.session.get(f"https://nhentai.net/g/{id}") as response:
            if response.ok:
                html: str = await response.text(encoding="utf-8")
                soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
                return cls(soup)
