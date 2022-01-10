from typing import Optional, List
from urllib import parse

import discord
from bs4 import BeautifulSoup

from core import bot


async def search(query: str) -> List[str]:
    """This function is a coroutine

    Search zerochan.net for a list of image URLs.

    Parameters
    -----
    query: ``str``
        The searching query

    Returns
    List[``str``]
        A list of image URLs
    """
    url: str = "https://www.zerochan.net/" + parse.quote(query, encoding="utf-8")
    ret: List[str] = []
    async with bot.session.get(url) as response:
        if response.ok:
            html: str = await response.text(encoding="utf-8")
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
            for img in soup.find_all("img"):
                image_url: Optional[str] = img.get("src")  # This should be "type: str" (who would create an <img> tag without "src" anyway?)
                if image_url.endswith(".jpg"):
                    ret.append(image_url)

    return ret
