from __future__ import annotations

import asyncio
import datetime
import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import aiohttp
import discord
from discord.utils import escape_markdown as escape
from yarl import URL

from .errors import CodeforcesException
from lib import utils


__all__ = (
    "PartialUser",
    "User",
)


def _ensure_valid_url(url: str) -> str:
    if url.startswith("//"):
        return "https:" + url


def _get_rating_color(rank: str) -> int:
    rank = rank.removeprefix("international ")
    colors = {
        "newbie": 0x808080,
        "pupil": 0x008000,
        "specialist": 0x03a89e,
        "expert": 0x0000ff,
        "candidate master": 0xaa00aa,
        "master": 0xff8c00,
        "grandmaster": 0xff0000,
        "legendary grandmaster": 0x000000,
    }

    return colors.get(rank, 0xffffff)


class PartialUser:
    """Represents a CodeForces user when just a handle is available"""

    if TYPE_CHECKING:
        handle: str

    def __init__(self, handle: str) -> None:
        self.handle = handle
        self.__fetched = None

    @property
    def url(self) -> str:
        return f"https://codeforces.com/profile/{self.handle}"

    async def fetch(self, *, session: aiohttp.ClientSession) -> User:
        if self.__fetched:
            return self.__fetched

        self.__fetched = await User.get(self.handle, session=session)
        return self.__fetched


class User(PartialUser):
    """Represents a CodeForces user"""

    if TYPE_CHECKING:
        email: Optional[str]
        vk_id: Optional[str]
        open_id: Optional[str]
        first_name: Optional[str]
        last_name: Optional[str]
        country: Optional[str]
        city: Optional[str]
        organization: Optional[str]
        contribution: int
        rank: Optional[str]  # Can be None for Unrated users
        rating: Optional[int]  # Can be None for Unrated users
        max_rank: Optional[str]  # Can be None for Unrated users
        max_rating: Optional[int]  # Can be None for Unrated users
        last_online: datetime.datetime
        registration_time: datetime.datetime
        friends_count: int
        avatar_url: str
        title_url: str

    def __init__(self, data: Dict[str, Any]) -> None:
        self.handle = data["handle"]
        self.email = data.get("email")
        self.vk_id = data.get("vkId")
        self.open_id = data.get("openId")
        self.first_name = data.get("firstName")
        self.last_name = data.get("lastName")
        self.country = data.get("country")
        self.city = data.get("city")
        self.organization = data.get("organization")
        self.contribution = data["contribution"]
        self.rank = data.get("rank")
        self.rating = data.get("rating")
        self.max_rank = data.get("maxRank")
        self.max_rating = data.get("maxRating")
        self.last_online = utils.from_unix_format(data["lastOnlineTimeSeconds"])
        self.registration_time = utils.from_unix_format(data["registrationTimeSeconds"])
        self.friends_count = data["friendOfCount"]
        self.avatar_url = _ensure_valid_url(data["avatar"])
        self.title_url = _ensure_valid_url(data["titlePhoto"])

    def create_embed(self) -> discord.Embed:
        descriptions = []
        if self.email is not None:
            descriptions.append(f"**Email** {self.email}")

        if self.vk_id is not None:
            descriptions.append(f"**ID for VK social network** {self.vk_id}")

        if self.open_id is not None:
            descriptions.append(f"**Open ID** {self.open_id}")

        if self.first_name or self.last_name:
            name_display = ["**Name**"]

            if self.first_name:
                name_display.append(self.first_name)

            if self.last_name:
                name_display.append(self.last_name)

            descriptions.append(" ".join(name_display))

        if self.country is not None:
            descriptions.append(f"**Country** {self.country}")

        if self.city is not None:
            descriptions.append(f"**City** {self.city}")

        if self.organization is not None:
            descriptions.append(f"**Organization** {self.organization}")

        embed = discord.Embed(
            title=escape(self.handle),
            description="\n".join(descriptions) if descriptions else None,
            color=_get_rating_color(self.rank),
            url=self.url,
            timestamp=self.registration_time,
        )
        embed.add_field(name="Contribution", value=self.contribution)
        embed.add_field(name="Rank", value=f"{self.rank} (max. {self.max_rank})" if self.max_rank is not None else "*Unknown*")
        embed.add_field(name="Rating", value=f"{self.rating} (max. {self.max_rating})" if self.max_rating is not None else "*Unknown*")
        embed.add_field(name="Friends Count", value=f"{self.friends_count}", inline=False)

        last_online = discord.utils.utcnow() - self.last_online
        embed.add_field(name="Last online", value=f"{utils.format(last_online.total_seconds())} ago")
        embed.set_footer(text="Registered on")
        embed.set_thumbnail(url=self.title_url)
        return embed

    @classmethod
    async def get(cls, *handles: str, session: aiohttp.ClientSession) -> Optional[List[User]]:
        query = ";".join(handles)
        url = URL.build(
            scheme="https",
            host="codeforces.com",
            path="/api/user.info",
            query_string=f"handles={query}",
        )
        try:
            async with session.get(url) as response:
                data = await response.json(encoding="utf-8")
                if data["status"] == "FAILED":
                    raise CodeforcesException(data["comment"])

                return [cls(payload) for payload in data["result"]]

        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise CodeforcesException("Unable to connect to codeforces.com")

        except json.JSONDecodeError:
            raise CodeforcesException("Cannot parse received data from codeforces.com")
