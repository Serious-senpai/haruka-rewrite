from __future__ import annotations

from typing import Any, Dict, Optional, Type, TYPE_CHECKING

import aiohttp


__all__ = (
    "PartialUser",
    "PixivUser",
)


class BaseUser:

    if TYPE_CHECKING:
        id: int
        name: str

    @property
    def url(self) -> str:
        return f"https://www.pixiv.net/en/users/{self.id}"

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
