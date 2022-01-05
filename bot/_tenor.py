from urllib import parse
from typing import List

from bs4 import BeautifulSoup

from core import bot


async def search(query: str) -> List[str]:
    """This function is a coroutine

    Search for image URLs from tenor

    Parameters
    -----
    query: ``str``
        The searching query

    Returns
    -----
    List[``str``]
        A list of result image URLs
    """
    url: str = "https://tenor.com/search/" + parse.quote(query, encoding="utf-8")
    ret: List[str] = []
    async with bot.session.get(url) as response:
        if response.ok:
            html: str = await response.text(encoding="utf-8")
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("figure", attrs={"class": "GifListItem"}):
                if img := tag.find("img"):
                    if image_url := img.get("src"):
                        if image_url.startswith("https://"):
                            ret.append(image_url)

    return ret
