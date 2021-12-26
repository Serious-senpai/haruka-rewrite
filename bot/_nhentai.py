from typing import List, Optional

import bs4
import discord
from discord.utils import escape_markdown as escape


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
        try:
            return self.soup.find("img").get("data-src")
        except AttributeError:
            return

    @property
    def thumb(self) -> Optional[str]:
        return self.thumbnail

    @property
    def path(self) -> str:
        return self.soup.find("a").get("href")

    @property
    def id(self) -> int:
        return int(self.path.split("/")[2])


class NHentai:
    """Represents a doujin from nhentai.net"""

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
        try:
            return self.soup.find("img").get("data-src")
        except AttributeError:
            pass

    @property
    def thumb(self) -> Optional[str]:
        return self.thumbnail

    @property
    def title(self) -> str:
        return self.soup.find("h1", attrs={"class": "title"}).find("span", attrs={"class": "pretty"}).get_text()

    @property
    def subtitle(self) -> Optional[str]:
        try:
            return self.soup.find("h2", attrs={"class": "title"}).find("span", attrs={"class": "pretty"}).get_text()
        except BaseException:
            return

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
