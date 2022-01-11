from typing import Dict, List, Optional

import bs4

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
    ret: List[str] = []
    url: str = "https://danbooru.donmai.us/posts"
    page: int = 0

    while page := page + 1:
        ext: List[str] = []
        params: Dict[str, str] = {
            "page": page,
            "tags": query,
        }

        async with bot.session.get(url, params=params) as response:
            if response.ok:
                html: str = await response.text(encoding="utf-8")
                soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
                for img in soup.find_all("img"):
                    path: Optional[str] = img.get("src")
                    if path.startswith("https://"):
                        ext.append(path)

        if ext:
            ret.extend(ext)
            if len(ret) >= max_results:
                return ret[:max_results]
        else:
            break

    return ret
