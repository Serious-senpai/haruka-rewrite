import asyncio
import contextlib
from typing import List

import aiohttp
import yarl
from bs4 import BeautifulSoup


async def search(query: str, *, max_results: int = 200, session: aiohttp.ClientSession) -> List[str]:
    """This function is a coroutine

    Search zerochan.net for a list of image URLs.

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
    url = yarl.URL.build(scheme="https", host="zerochan.net", path=f"/{query}")
    ret = []
    page = 0

    with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
        while True:
            page += 1
            ext = []

            async with session.get(url.with_query(p=page)) as response:
                if response.ok:
                    html = await response.text(encoding="utf-8")
                    soup = BeautifulSoup(html, "html.parser")
                    for img in soup.find_all("img"):
                        image_url = img.get("src")  # This should be "type: str" (who would create an <img> tag without "src" anyway?)
                        if image_url.endswith(".jpg"):
                            ext.append(image_url)

            if ext:
                ret.extend(ext)
                if len(ret) >= max_results:
                    return ret[:max_results]
            else:
                break

    return ret
