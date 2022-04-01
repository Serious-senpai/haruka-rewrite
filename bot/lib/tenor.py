from typing import List

import aiohttp
import yarl
from bs4 import BeautifulSoup


async def search(query: str, *, session: aiohttp.ClientSession) -> List[str]:
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
    url = yarl.URL.build(scheme="https", host="tenor.com", path=f"/search/{query}")
    ret = []
    async with session.get(url) as response:
        if response.ok:
            html = await response.text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("figure", attrs={"class": "GifListItem"}):
                if img := tag.find("img"):
                    if image_url := img.get("src"):
                        if image_url.startswith("https://"):
                            ret.append(image_url)

    return ret
