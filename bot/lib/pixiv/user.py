from __future__ import annotations

import re
from typing import Any, Dict, Optional, Type, TYPE_CHECKING

import aiohttp


__all__ = ("USER_PATTERN", "PartialUser", "PixivUser")
USER_PATTERN = re.compile(r"https://www\.pixiv\.net/(en/)?users/(\d+)/?.*")


class BaseUser:

    if TYPE_CHECKING:
        id: int
        name: str

    @property
    def url(self) -> str:
        """Link to the user's Pixiv page"""
        return f"https://www.pixiv.net/en/users/{self.id}"

    @property
    def artworks_url(self) -> str:
        """Link to the user's Pixiv artworks page"""
        return f"https://www.pixiv.net/en/users/{self.id}/artworks"

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name}>"


class PartialUser(BaseUser):
    """Represents a Pixiv user when only ID and username are available"""

    __slots__ = ("id", "name")

    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

    async def fetch(self, *, session: aiohttp.ClientSession) -> Optional[PixivUser]:
        """This function is a coroutine

        Fetch this ``PartialUser`` to a full ``PixivUser`` object.

        Parameters
        -----
        session: ``aiohttp.ClientSession``
            The session to perform the request

        Returns
        -----
        Optional[``PixivUser``]
            The retrieved user, or ``None`` if any errors occurred
        """
        return await PixivUser.get(self.id, session=session)


class PixivUser(BaseUser):
    """Represents a Pixiv user"""

    __slots__ = ("id", "name", "image_url", "accept_request")
    if TYPE_CHECKING:
        image_url: str
        accept_request: bool

    def __init__(self, data: Dict[str, Any]) -> None:
        self.id = data["userId"]
        self.name = data["name"]
        self.image_url = data["imageBig"]
        self.accept_request = data["acceptRequest"]

    @classmethod
    async def get(cls: Type[PixivUser], user_id: int, *, session: aiohttp.ClientSession) -> Optional[PixivUser]:
        """This function is a coroutine

        Get a ``PixivUser`` from an ID

        Parameters
        -----
        user_id: ``int``
            The user ID
        session: ``aiohttp.ClientSession``
            The session to perform the request

        Returns
        -----
        Optional[``PixivUser``]
            The retrieved user, or ``None`` if not found
        """
        async with session.get(f"https://www.pixiv.net/ajax/user/{user_id}") as response:
            if response.status != 200:
                return

            data = await response.json(encoding="utf-8")
            if data["error"]:
                return

            return cls(data["body"])

    @classmethod
    async def from_url(cls: Type[PixivUser], url: str, *, session: aiohttp.ClientSession) -> Optional[PixivUser]:
        match = USER_PATTERN.fullmatch(url)
        if not match:
            return

        return await cls.get(int(match.group(2)), session=session)
