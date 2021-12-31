from __future__ import annotations

from typing import List, Optional, Type

import bs4
import discord

from core import bot


class SauceResult:

    __slots__ = (
        "similarity",
        "thumbnail_url",
        "title",
        "url",
    )

    def __init__(self, *,similarity: str, thumbnail_url: str, title: str, url: str) -> None:
        self.similarity: str = similarity
        self.thumbnail_url: str = thumbnail_url
        self.title: str = title
        self.url: str = url

    def create_embed(self) -> discord.Embed:
        embed: discord.Embed = discord.Embed(
            title=self.title,
            description=self.url,
        )
        embed.set_thumbnail(url=self.thumbnail_url)
        embed.add_field(
            name="Similarity",
            value=self.similarity,
        )
        return embed

    @classmethod
    async def get_sauce(cls: Type[SauceResult], url: str) -> List[SauceResult]:
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

    try:
        thumbnail_url: str = table.find("div", attrs={"class": "resultimage"}).find("img").get("src")

        content: bs4.Tag = table.find("td", attrs={"class": "resulttablecontent"})
        title: str = content.find("div", attrs={"class": "resulttitle"}).get_text()
        similarity: str = content.find("div", attrs={"class": "resultsimilarityinfo"}).get_text()
        url: str = content.find("div", attrs={"class": "resultcontentcolumn"}).find("a").get("href")
        return SauceResult(similarity=similarity, thumbnail_url=thumbnail_url, title=title, url=url)
    except BaseException:
        return
