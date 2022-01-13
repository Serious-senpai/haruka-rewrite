from __future__ import annotations

import contextlib
import traceback
from typing import Optional, Type, TYPE_CHECKING

import aiohttp
import bs4
import discord
from discord.utils import escape_markdown as escape

from core import bot


class UrbanSearch:
    """Represents a search result from Urban Dictionary"""

    __slots__ = ("title", "meaning", "example", "url")
    if TYPE_CHECKING:
        title: str
        meaning: str
        example: str
        url: str

    def __init__(
        self,
        title: str,
        meaning: str,
        example: str,
        url: str,
    ) -> None:
        self.title = title
        self.meaning = meaning
        self.example = example
        self.url = url

    def create_embed(self) -> discord.Embed:
        meaning = escape(self.meaning)
        example = escape(self.example)
        title = escape(self.title)
        desc = f"{meaning}\n---------------\n{example}"

        if len(desc) > 4096:
            desc = desc[:4090] + " [...]"

        em = discord.Embed(
            title=f"{title}",
            description=desc,
            url=self.url,
        )
        em.set_footer(text="From Urban Dictionary")

        return em

    def __repr__(self) -> str:
        return f"<UrbanSearch title={self.title} meaning={self.meaning[:50]}>"

    @classmethod
    async def search(cls: Type[UrbanSearch], word: str) -> Optional[UrbanSearch]:
        url = f"https://www.urbandictionary.com/define.php"
        for _ in range(10):
            try:
                async with bot.session.get(url, params={"term": word}) as response:
                    if response.status == 200:
                        html = await response.text(encoding="utf-8")
                        html = html.replace("<br/>", "\n").replace("\r", "\n")
                        soup = bs4.BeautifulSoup(html, "html.parser")
                        obj = soup.find(name="h1")
                        title = obj.get_text()

                        meaning = ""
                        example = ""

                        with contextlib.suppress(AttributeError):
                            obj = soup.find(name="div", attrs={"class": "meaning"})
                            meaning = "\n".join(i for i in obj.get_text().split("\n") if len(i) > 0)

                        with contextlib.suppress(AttributeError):
                            obj = soup.find(name="div", attrs={"class": "example"})
                            example = "\n".join(i for i in obj.get_text().split("\n") if len(i) > 0)

                        return cls(title, meaning, example, response.url)
                    else:
                        return

            except aiohttp.ClientError:
                bot.log(traceback.format_exc())
                await bot.report("An `aiohttp.ClientError` exception has just occurred from `urban` module.", send_state=False)
                continue
