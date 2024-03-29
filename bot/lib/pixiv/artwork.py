from __future__ import annotations

import asyncio
import contextlib
import enum
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union, TYPE_CHECKING

import aiohttp
import discord
from discord.utils import escape_markdown as escape

from env import HOST
from lib.utils import AsyncSequence
from .tags import PixivArtworkTag
from .user import PartialUser


__all__ = ("ImageType", "PixivArtwork",)
PIXIV_HEADERS = {"referer": "https://www.pixiv.net/"}


class ImageType(enum.Enum):
    MINI = "mini"
    THUMB = "thumb"
    SMALL = "small"
    REGULAR = "regular"
    ORIGINAL = "original"


class PixivArtwork:
    """Represents a Pixiv artwork"""

    __slots__ = (
        "id",
        "title",
        "author",
        "nsfw",
        "created_at",
        "tags",
        "width",
        "height",
        "pages_count",
        "completed",
        "_image_urls",
    )
    if TYPE_CHECKING:
        id: int
        title: str
        author: PartialUser
        nsfw: bool
        created_at: datetime
        tags: Union[List[str], List[PixivArtworkTag]]
        width: int
        height: int
        pages_count: int
        completed: bool
        _image_urls: Dict[ImageType, str]

    def __init__(self, data: Dict[str, Any]) -> None:
        self.id = int(data["id"])
        self.title = data["title"]
        self.author = PartialUser(data["userId"], data["userName"])
        self.nsfw = bool(data["xRestrict"])
        self.created_at = datetime.fromisoformat(data["createDate"])

        self._image_urls = {}
        if "urls" in data:
            for image_type in ImageType:
                if image_type.value in data["urls"]:
                    self._image_urls[image_type] = data["urls"][image_type.value]

            self.completed = True
        else:
            self._image_urls[ImageType.REGULAR] = data["url"]
            self.completed = False

        if isinstance(data["tags"], dict):
            tags = data["tags"]["tags"]
            self.tags = [PixivArtworkTag(d) for d in tags]
        else:
            self.tags = data["tags"]

        self.width = data["width"]
        self.height = data["height"]
        self.pages_count = data["pageCount"]

    def image(self, image_type: ImageType) -> Optional[str]:
        return self._image_urls.get(image_type)

    @property
    def url(self) -> str:
        return f"https://www.pixiv.net/en/artworks/{self.id}"

    @property
    def image_url(self) -> str:
        return self._image_urls[ImageType.REGULAR]

    async def update(self, *, session: aiohttp.ClientSession) -> None:
        """This function is a coroutine

        Update this artwork data

        Parameters
        -----
        session: ``aiohttp.ClientSession``
            The session to perform the update
        """
        artwork = await PixivArtwork.get(self.id, session=session)
        for attr in self.__slots__:
            setattr(self, attr, getattr(artwork, attr))

    async def save(self, image_type: ImageType = ImageType.REGULAR, *, session: aiohttp.ClientSession) -> bool:
        """This function is a coroutine

        Save this artwork to the local machine, which is exposed
        to the server side.

        Parameters
        -----
        image_type: ``ImageType``
            The type of the image to download
        session: ``aiohttp.ClientSession``
            The session to perform the request

        Returns
        -----
        ``bool``
            Whether the operation was successful
        """
        if os.path.isfile(f"./server/images/{self.id}.png"):
            return True

        if not self.completed:
            await self.update(session=session)

        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            async with session.get(self.image(image_type), headers=PIXIV_HEADERS) as response:
                if response.ok:
                    with open(f"./server/images/{self.id}.png", "wb") as f:
                        f.write(await response.read())

                    return True

        return False

    async def create_embed(self, *, session: aiohttp.ClientSession) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            url=self.url,
            timestamp=self.created_at,
        )

        if await self.save(session=session):
            embed.set_image(url=f"{HOST}/images/{self.id}.png")
        else:
            embed.set_image(url="https://s.pximg.net/www/images/pixiv_logo.png")

        if self.tags:
            embed.add_field(
                name="Tags",
                value=", ".join(f"[{str(tag)}]({tag.url})" for tag in self.tags),
                inline=False,
            )

        embed.add_field(
            name="Artwork ID",
            value=self.id,
        )
        embed.add_field(
            name="Author",
            value=f"[{escape(self.author.name)}]({self.author.url})",
        )
        embed.add_field(
            name="Size",
            value=f"{self.width} x {self.height}",
        )
        embed.add_field(
            name="Pages count",
            value=self.pages_count,
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
    async def get(cls: Type[PixivArtwork], artwork_id: int, *, session: aiohttp.ClientSession) -> Optional[PixivArtwork]:
        """This function is a coroutine

        Get a ``PixivArtwork`` from an ID

        Parameters
        -----
        artwork_id: ``int``
            The artwork ID
        session: ``aiohttp.ClientSession``
            The session to perform the request

        Returns
        -----
        Optional[``PixivArtwork``]
            The retrieved artwork, or ``None`` if not found
        """
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            async with session.get(f"https://www.pixiv.net/ajax/illust/{artwork_id}") as response:
                if response.status != 200:
                    return

                data = await response.json(encoding="utf-8")
                if data["error"]:
                    return

                return cls(data["body"])

    @classmethod
    async def from_user(cls: Type[PixivArtwork], user_id: int, *, session: aiohttp.ClientSession) -> AsyncSequence[Optional[PixivArtwork]]:
        """This function is a coroutine

        Retrieve a number of artworks of a Pixiv user

        Parameters
        -----
        user_id: ``int``
            The user ID to retrieve artworks from
        session: ``aiohttp.ClientSession``
            The session to perform the search

        Returns
        -----
        AsyncSequence[Optional[``PixivArtwork``]]
            The collected list of artworks, this may be empty
        """
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            async with session.get(f"https://www.pixiv.net/ajax/user/{user_id}/profile/all?lang=en") as response:
                if response.status != 200:
                    return AsyncSequence([])

                data = await response.json(encoding="utf-8")
                if data["error"]:
                    return AsyncSequence([])

                return AsyncSequence([cls.get(artwork_id, session=session) for artwork_id in data["body"]["illusts"].keys()])

        return AsyncSequence([])

    @classmethod
    async def search(cls: Type[PixivArtwork], query: str, *, session: aiohttp.ClientSession) -> List[PixivArtwork]:
        """This function is a coroutine

        Get 6 Pixiv images sorted by date that match the searching query.

        Parameters
        -----
        query: ``str``
            The searching query
        session: ``aiohttp.ClientSession``
            The session to perform the search

        Returns
        -----
        List[``PixivArtwork``]
            A list of search results, note that this may be empty
        """
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            async with session.get(f"https://www.pixiv.net/ajax/search/artworks/{query}") as response:
                if response.ok:
                    data = await response.json(encoding="utf-8")
                    try:
                        artworks = data["body"]["illustManga"]["data"]
                    except KeyError:
                        pass
                    else:
                        return [cls(artwork) for artwork in artworks[:6]]

        return []
