from __future__ import annotations

import asyncio
import datetime
import json
from typing import Any, Dict, List, Literal, Optional, Type, TYPE_CHECKING

import aiohttp
import discord

from .errors import CodeforcesException
from .users import PartialUser
from lib import utils


__all__ = (
    "Contest",
)


class Contest:

    if TYPE_CHECKING:
        id: int
        name: str
        type: Literal["CF", "IOI", "ICPC"]
        phase: Literal["BEFORE", "CODING", "PENDING_SYSTEM_TEST", "SYSTEM_TEST", "FINISHED"]
        frozen: bool
        duration: datetime.timedelta
        start_at: Optional[datetime.datetime]
        relative_time: Optional[datetime.timedelta]
        prepared_by: Optional[PartialUser]
        _url: Optional[str]
        description: Optional[str]
        difficulty: Optional[Literal[1, 2, 3, 4, 5]]
        kind: Optional[str]
        icpc_region: Optional[str]
        country: Optional[str]
        city: Optional[str]
        season: Optional[str]

    def __init__(self, data: Dict[str, Any]) -> None:
        self.id = data["id"]
        self.name = data["name"]
        self.type = data["type"]
        self.phase = data["phase"]
        self.frozen = data["frozen"]
        self.duration = datetime.timedelta(seconds=data["durationSeconds"])

        start_at = data.get("startTimeSeconds")
        if start_at is not None:
            self.start_at = utils.from_unix_format(start_at)
        else:
            self.start_at = None

        relative_time = data.get("relativeTimeSeconds")
        if relative_time is not None:
            self.relative_time = datetime.timedelta(seconds=relative_time)
        else:
            self.relative_time = None

        prepared_by = data.get("preparedBy")
        if prepared_by is not None:
            self.prepared_by = PartialUser(prepared_by)
        else:
            self.prepared_by = None

        self._url = data.get("websiteUrl")
        self.description = data.get("description")

        difficulty = data.get("difficulty")
        if difficulty is not None:
            self.difficulty = int(difficulty)
        else:
            self.difficulty = None

        self.kind = data.get("kind")
        self.icpc_region = data.get("icpcRegion")
        self.country = data.get("country")
        self.city = data.get("city")
        self.season = data.get("season")

    @property
    def url(self) -> str:
        if self._url:
            return self._url

        return f"https://codeforces.com/contest/{self.id}"

    def create_embed(self) -> discord.Embed:
        descriptions = []
        if self.description is not None:
            descriptions.append(self.description)

        if self.country is not None:
            descriptions.append(f"**Country** {self.country}")

        if self.city is not None:
            descriptions.append(f"**City** {self.city}")

        if self.season is not None:
            descriptions.append(f"**Season** {self.season}")

        embed = discord.Embed(
            title=self.name,
            description="\n".join(descriptions) if descriptions else None,
            url=self.url,
            timestamp=self.start_at,
        )

        if self.relative_time is not None:
            seconds = self.relative_time.total_seconds()
            if seconds >= 0:
                embed.add_field(name="Started at", value=f"{utils.format(seconds)} ago", inline=False)
            else:
                embed.add_field(name="Starts at", value=f"{utils.format(-seconds)} later", inline=False)

        embed.add_field(name="Type", value=self.type)
        embed.add_field(name="Phase", value=self.phase)
        embed.add_field(name="Duration", value=utils.format(self.duration.total_seconds()))

        if self.prepared_by is not None:
            embed.add_field(name="Prepared by", value=self.prepared_by.handle)

        if self.difficulty is not None:
            embed.add_field(name="Difficulty (1 to 5)", value=self.difficulty)

        if self.kind is not None:
            embed.add_field(name="Kind", value=self.kind)

        if self.icpc_region is not None:
            embed.add_field(name="ICPC Region", value=self.icpc_region)

        return embed

    @classmethod
    async def list(cls: Type[Contest], *, gym: bool = False, session: aiohttp.ClientSession) -> List[Contest]:
        url = "https://codeforces.com/api/contest.list"
        try:
            async with session.get(url, params={"gym": str(gym).lower()}) as response:
                data = await response.json(encoding="utf-8")
                if data["status"] == "FAILED":
                    raise CodeforcesException(data["comment"])

                return [cls(payload) for payload in data["result"]]

        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise CodeforcesException("Unable to connect to codeforces.com")

        except json.JSONDecodeError:
            raise CodeforcesException("Cannot parse received data from codeforces.com")
