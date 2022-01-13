import contextlib
from typing import List

import aiohttp
from bs4 import BeautifulSoup

from core import bot


async def search(query: str, *, max_results: int = 200) -> List[str]:
    """This function is a coroutine

    Search danbooru for a list of image URLs.

    Parameters
    -----
    query: ``str``
        The searching query
    max_results: ``int``
        The maximum number of results to return

    Returns
    List[``str``]
        A list of image URLs
    """
    ret = []
    url = "https://danbooru.donmai.us/posts"
    page = 0

    with contextlib.suppress(aiohttp.ClientError):
        while page := page + 1:
            ext = []
            params = {
                "page": page,
                "tags": query,
            }

            async with bot.session.get(url, params=params) as response:
                if response.ok:
                    html = await response.text(encoding="utf-8")
                    soup = BeautifulSoup(html, "html.parser")
                    for img in soup.find_all("img"):
                        path = img.get("src")
                        if path.startswith("https://"):
                            ext.append(path)

            if ext:
                ret.extend(ext)
                if len(ret) >= max_results:
                    return ret[:max_results]
            else:
                break

    return ret
