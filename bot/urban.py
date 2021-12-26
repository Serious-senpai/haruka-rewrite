from __future__ import annotations

import traceback
from typing import Optional, Type

import aiohttp
import bs4
import discord
from discord.utils import escape_markdown as escape

from core import bot


class UrbanSearch:

    __slots__ = (
        "_title",
        "_meaning",
        "_example",
        "_url",
    )

    def __init__(
        self,
        title: str,
        meaning: str,
        example: str,
        url: str,
    ) -> None:
        self._title: str = title
        self._meaning: str = meaning
        self._example: str = example
        self._url: str = url

    @property
    def title(self) -> str:
        return self._title

    @property
    def meaning(self) -> str:
        return self._meaning

    @property
    def example(self) -> str:
        return self._example

    @property
    def url(self) -> str:
        return self._url

    def create_embed(self) -> discord.Embed:
        meaning: str = escape(self.meaning)
        example: str = escape(self.example)
        title: str = escape(self.title)
        desc: str = f"{meaning}\n---------------\n{example}"

        if len(desc) > 4096:
            desc = desc[:4090] + " [...]"

        em: discord.Embed = discord.Embed(
            title=f"{title}",
            description=desc,
            url=self.url,
        )
        em.set_footer(text="From Urban Dictionary")

        return em

    @classmethod
    async def search(cls: Type[UrbanSearch], word: str) -> Optional[UrbanSearch]:
        url: str = f"https://www.urbandictionary.com/define.php"
        params = {
            "term": word,
        }
        for _ in range(10):
            try:
                async with bot.session.get(url, params=params) as response:
                    if response.status == 200:
                        html: str = await response.text(encoding="utf-8")
                        html = html.replace("<br/>", "\n").replace("\r", "\n")
                        soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
                        obj: bs4.Tag = soup.find(name="div", attrs={"class": "def-header"})
                        title: str = obj.get_text()

                        meaning: Optional[str]
                        example: Optional[str]

                        try:
                            obj = soup.find(name="div", attrs={"class": "meaning"})
                            meaning = "\n".join(i for i in obj.get_text().split("\n") if len(i) > 0)
                        except BaseException:
                            meaning = None

                        try:
                            obj = soup.find(name="div", attrs={"class": "example"})
                            example = "\n".join(i for i in obj.get_text().split("\n") if len(i) > 0)
                        except BaseException:
                            example = None
                        return cls(title, meaning, example, response.url)
                    else:
                        return

            except aiohttp.ClientError:
                bot.log(traceback.format_exc())
                await bot.report("An `aiohttp.ClientError` exception has just occurred from `urban` module.", send_state=False)
                continue
