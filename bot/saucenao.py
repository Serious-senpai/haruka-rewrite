from __future__ import annotations

import contextlib
from typing import List, Optional, Type

import bs4
import discord
from discord.utils import escape_markdown as escape

from core import bot


class SauceResult:
    """Represents a search result from saucenao

    Attributes
    -----
    similarity: ``str``
        A string that displays the similarity between the initial image and the
        searched one (e.g. ``95.95%``)
    thumbnail_url: ``str``
        The URL to the small-size searched image, suitable for embedding as
        thumbnail
    title: ``str``
        The title of the search result
    url: ``str``
        The URL to the source of the image (pixiv, twitter,...)
    """

    __slots__ = (
        "similarity",
        "thumbnail_url",
        "title",
        "url",
    )

    def __init__(self, *, similarity: str, thumbnail_url: str, title: str, url: str) -> None:
        self.similarity: str = similarity
        self.thumbnail_url: str = thumbnail_url
        self.title: str = title
        self.url: str = url

    def create_embed(self) -> discord.Embed:
        """Create an embed displaying this search result

        Returns
        -----
        ``discord.Embed``
            The created embed
        """
        embed: discord.Embed = discord.Embed(
            title=escape(self.title),
            description=self.url,
            url=self.url,
        )
        embed.set_thumbnail(url=self.thumbnail_url)
        embed.add_field(
            name="Similarity",
            value=self.similarity,
        )
        return embed

    @classmethod
    async def get_sauce(cls: Type[SauceResult], url: str) -> List[SauceResult]:
        """This function is a coroutine

        Get the sauce for an image from its URL

        Parameters
        -----
        url: ``str``
            The URL of the initial image

        Returns
        -----
        List[``SauceResult``]
            A list of searched results from saucenao, sorted by similarity
        """
        ret: List[SauceResult] = []
        async with bot.session.post("https://saucenao.com/search.php", data={"url": url}) as response:
            if response.ok:
                html: str = await response.text(encoding="utf-8")
                soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
                results: bs4.element.ResultSet[bs4.BeautifulSoup] = soup.find_all(name="div", attrs={"class": "result"})
                for result in results:
                    if "hidden" in result.get("class", []):
                        continue

                    r: Optional[SauceResult] = parse_result(result)
                    if r is not None:
                        ret.append(r)

        return ret


def parse_result(html: bs4.BeautifulSoup) -> Optional[SauceResult]:
    table: Optional[bs4.Tag] = html.find("table", attrs={"class": "resulttable"})
    if not table:
        return

    with contextlib.suppress(AttributeError):
        thumbnail_url: str = table.find("div", attrs={"class": "resultimage"}).find("img").get("src")

        content: bs4.Tag = table.find("td", attrs={"class": "resulttablecontent"})
        title: str = content.find("div", attrs={"class": "resulttitle"}).get_text()
        similarity: str = content.find("div", attrs={"class": "resultsimilarityinfo"}).get_text()
        url: str = content.find("div", attrs={"class": "resultcontentcolumn"}).find("a").get("href")
        return SauceResult(similarity=similarity, thumbnail_url=thumbnail_url, title=title, url=url)
