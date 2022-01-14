from __future__ import annotations

import json
import os
import re
import traceback
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

import bs4
import discord
from discord.utils import escape_markdown as escape

from core import bot


PIXIV_HEADERS = {"referer": "https://www.pixiv.net/"}
ID_PATTERN = re.compile(r"(?<!\d)\d{8}(?!\d)")
CHUNK_SIZE = 4 << 10


class PixivUser:
    """Represents a Pixiv user"""

    __slots__ = ("id", "name", "image_url")
    if TYPE_CHECKING:
        id: int
        name: str
        image_url: str

    def __init__(self, id: int, name: str, image_url: str) -> None:
        self.id = id
        self.name = name
        self.image_url = image_url

    def __repr__(self) -> str:
        return f"<PixivUser name={self.name} id={self.id}>"


class PixivArtwork:
    """Represents an artwork from Pixiv ajax"""

    __slots__ = ("title", "id", "image_url", "width", "height", "nsfw", "description", "tags", "url", "thumbnail", "author")
    if TYPE_CHECKING:
        title: str
        id: int
        image_url: str
        width: int
        height: int
        nsfw: bool
        description: Optional[str]
        tags: Optional[List[str]]
        url: str
        thumbnail: str
        author: PixivUser

    def __init__(self, json: Dict[str, Any]) -> None:
        self.title = json["title"]
        self.id = json["id"]
        self.image_url = json["url"]
        self.width = json["width"]
        self.height = json["height"]

        self.nsfw = json.get("xRestrict", False)
        self.description = json.get("description")
        self.tags = json.get("tags")
        self.url = f"https://www.pixiv.net/en/artworks/{self.id}"
        self.thumbnail = f"https://embed.pixiv.net/decorate.php?illust_id={self.id}"

        author_id = json["userId"]
        author_name = json["userName"]
        author_avatar_url = json["profileImageUrl"]
        self.author = PixivUser(author_id, author_name, author_avatar_url)

    async def stream(self) -> None:
        if os.path.isfile(f"./server/image/{self.id}.png"):
            return

        async with bot.session.get(
            self.image_url,
            headers=PIXIV_HEADERS,
        ) as response:
            if response.ok:
                with open(f"./server/image/{self.id}.png", "wb", buffering=0) as f:
                    while data := await response.content.read(CHUNK_SIZE):
                        f.write(data)
            else:
                raise discord.HTTPException(response, f"Pixiv returned {response.status}")

    async def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.description) if self.description else discord.Embed.Empty,
            url=self.url,
        )

        try:
            await self.stream()
        except discord.HTTPException:
            embed.set_image(url=self.thumbnail)
            bot.log(traceback.format_exc())
        else:
            embed.set_image(url=f"{bot.HOST}/image/{self.id}.png")

        embed.add_field(
            name="Tags",
            value=", ".join(escape(tag) for tag in self.tags) if self.tags else "*No tags given*",
            inline=False,
        )
        embed.add_field(
            name="Artwork ID",
            value=self.id,
        )
        embed.add_field(
            name="Author",
            value=f"[{escape(self.author.name)}](https://www.pixiv.net/en/users/{self.author.id})",
        )
        embed.add_field(
            name="Size",
            value=f"{self.width} x {self.height}",
        )
        embed.add_field(
            name="Artwork link",
            value=self.url,
            inline=False,
        )
        return embed

    def __repr__(self) -> str:
        return f"<PixivArtwork title={self.title} id={self.id} author={self.author}>"

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
                html = await response.text(encoding="utf-8")
                soup = bs4.BeautifulSoup(html, "html.parser")
                content = soup.find("meta", attrs={"name": "preload-data"}).get("content")
                if content:
                    data = json.loads(content)
                    illust = data["illust"][str(id)]
                    user_id = int(illust.get("userId"))
                    ret = {
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
