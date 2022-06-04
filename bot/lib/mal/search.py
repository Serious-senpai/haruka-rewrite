from __future__ import annotations

from typing import List, Literal, Type, TYPE_CHECKING

import aiohttp
import bs4


__all__ = ("MALSearchResult",)


class MALSearchResult:
    """Represents a search result from MyAnimeList.

    Note that it can be anything: anime, manga,...
    """

    __slots__ = ("soup",)
    if TYPE_CHECKING:
        soup: bs4.BeautifulSoup

    def __init__(self, soup: bs4.BeautifulSoup) -> None:
        self.soup = soup

    @property
    def id(self) -> int:
        return int(self.url.split("/")[4])

    @property
    def url(self) -> str:
        return self.soup.get("href")

    @property
    def title(self) -> str:
        return self.soup.get_text()

    def __repr__(self) -> str:
        return f"<MALSearchResult id={self.id} title={self.title} url={self.url}>"

    @classmethod
    async def search(
        cls: Type[MALSearchResult],
        query: str,
        *,
        criteria: Literal["manga", "anime"],
        session: aiohttp.ClientSession
    ) -> List[MALSearchResult]:
        rslt = []
        url = f"https://myanimelist.net/{criteria}.php"

        async with session.get(url, params={"q": query}) as response:
            if response.status == 200:
                html = await response.text(encoding="utf-8")
                soup = bs4.BeautifulSoup(html, "html.parser")
                obj = soup.find_all(
                    name="td",
                    attrs={"class": "borderClass bgColor0"},
                    limit=12,
                )

                for index, tag in enumerate(obj):
                    if index % 2 == 0:
                        continue
                    rslt.append(cls(tag.find("a")))

        return rslt
