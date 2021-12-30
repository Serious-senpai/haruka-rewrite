from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Type

import bs4
import discord
from discord.utils import escape_markdown as escape

from core import bot


PIXIV_HEADERS: Dict[str, str] = {"referer": "https://www.pixiv.net/"}
ID_PATTERN: re.Pattern = re.compile(r"^(?<!\d)\d{8,8}(?!\d)$")
CHUNK_SIZE: int = 4 << 10


class PixivUser:
    """Represents a Pixiv user"""

    __slots__ = (
        "_id",
        "_name",
        "_image_url",
    )

    def __init__(self, id: int, name: str, image_url: str) -> None:
        self._id: int = id
        self._name: str = name
        self._image_url: str = image_url

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def image_url(self) -> str:
        # This URL must be fetched with an appropriate header to retrieve data
        return self._image_url


class PixivArtwork:
    """Represents an artwork from Pixiv ajax"""

    __slots__ = (
        "_json",
    )

    def __init__(self, json: Dict[str, Any]) -> None:
        self._json: Dict[str, Any] = json

    @property
    def json(self) -> Dict[str, Any]:
        return self._json

    @property
    def title(self) -> str:
        return self.json.get("title")

    @property
    def id(self) -> int:
        return self.json.get("id")

    @property
    def url(self) -> str:
        return f"https://www.pixiv.net/en/artworks/{self.id}"

    @property
    def nsfw(self) -> bool:
        return self.json.get("xRestrict", False)

    @property
    def image_url(self) -> str:
        # This URL must be fetched with an appropriate header to retrieve data
        return self.json.get("url")

    @property
    def thumbnail(self) -> str:
        # This URL returns a partial image of the artwork
        return f"https://embed.pixiv.net/decorate.php?illust_id={self.id}"

    @property
    def thumb(self) -> str:
        return self.thumbnail

    @property
    def description(self) -> str:
        # This string can (usually) be empty
        return self.json.get("description", "")

    @property
    def width(self) -> int:
        return self.json.get("width")

    @property
    def height(self) -> int:
        return self.json.get("height")

    @property
    def tags(self) -> Optional[List[str]]:
        return self.json.get("tags")

    @property
    def author(self) -> PixivUser:
        id = self.json.get("userId")
        name = self.json.get("userName")
        image_url = self.json.get("profileImageUrl")
        return PixivUser(id, name, image_url)

    async def stream(self) -> None:
        if os.path.isfile(f"./server/image/{self.id}.png"):
            return

        async with bot.session.get(
            self.image_url,
            headers=PIXIV_HEADERS,
        ) as response:
            if response.ok:
                with open(f"./server/image/{self.id}.png", "wb", buffering=0) as f:
                    data: bytes = await response.content.read(CHUNK_SIZE)
                    while data:
                        f.write(data)
                        data = await response.content.read(CHUNK_SIZE)
            else:
                raise discord.HTTPException(response, f"HTTP status code {response.status}")

    async def create_embed(self) -> discord.Embed:
        em: discord.Embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.description) if self.description else discord.Embed.Empty,
            url=self.url,
        )

        try:
            await self.stream()
        except discord.HTTPException:
            em.set_image(url=self.thumbnail)
        else:
            em.set_image(url=f"{bot.HOST}/image/{self.id}.png")

        em.add_field(
            name="Tags",
            value=", ".join(escape(tag) for tag in self.tags) if self.tags else "*No tags given*",
            inline=False,
        )
        em.add_field(
            name="Artwork ID",
            value=self.id,
        )
        em.add_field(
            name="Author",
            value=f"[{escape(self.author.name)}](https://www.pixiv.net/en/users/{self.author.id})",
        )
        em.add_field(
            name="Size",
            value=f"{self.width} x {self.height}",
        )
        em.add_field(
            name="Artwork link",
            value=self.url,
            inline=False,
        )
        return em

    @classmethod
    async def search(
        cls: Type[PixivArtwork],
        query: str,
    ) -> Optional[List[PixivArtwork]]:
        """Get 6 Pixiv images sorted by date that match the searching query."""
        async with bot.session.get(f"https://www.pixiv.net/ajax/search/artworks/{query}") as response:
            if response.ok:
                json = await response.json()
                try:
                    artworks = json["body"]["illustManga"]["data"]
                except KeyError:
                    return
                else:
                    return list(cls(artwork) for artwork in artworks[:6])
            else:
                return

    @classmethod
    async def from_id(
        cls: Type[PixivArtwork],
        id: int,
    ) -> Optional[PixivArtwork]:
        async with bot.session.get(f"https://pixiv.net/en/artworks/{id}") as response:
            if response.ok:
                html: str = await response.text(encoding="utf-8")
                soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
                content: Optional[str] = soup.find("meta", attrs={"name": "preload-data"}).get("content")
                if content:
                    data: Dict[str, Any] = json.loads(content)
                    illust: Dict[str, Any] = data["illust"][str(id)]
                    user_id: int = int(illust.get("userId"))
                    ret: Dict[str, Any] = {
                        "title": illust.get("title"),
                        "id": id,
                        "xRestrict": illust.get("xRestrict"),
                        "url": illust.get("urls", {}).get("regular", discord.Embed.Empty),
                        "tags": list(tag["tag"] for tag in illust["tags"]["tags"]),
                        "width": illust.get("width"),
                        "height": illust.get("height"),
                        "userId": user_id,
                        "userName": illust.get("userName"),
                        "profileImageUrl": data["user"][str(user_id)]["image"],
                    }
                    return cls(ret)
