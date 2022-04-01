from __future__ import annotations

import asyncio
import contextlib
import copy
import json
import os
import shlex
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

import aiohttp
import discord
from discord.utils import escape_markdown as escape

from lib.utils import format
from .constants import INVIDIOUS_URLS, TIMEOUT
if TYPE_CHECKING:
    from .client import AudioClient


__all__ = (
    "PartialInvidiousSource",
    "InvidiousSource",
)


def get_from_memory(id: str) -> Optional[Dict[str, Any]]:
    """Load snippet information about a track from a
    local JSON file.

    Since file operations are I/O bound, this function
    should be called in another thread.

    Parameters
    -----
    id: ``str``
        The track ID.

    Returns
    -----
    Optional[Dict[``str``, Any]]
        A dictionary containing the snippet information
        about the track, or ``None`` if not found.
    """
    if os.path.isfile(f"./tracks/{id}.json"):
        with open(f"./tracks/{id}.json", "r") as f:
            return json.load(f)


def save_to_memory(data: Dict[str, Any]) -> None:
    """Save snippet information about a track to a
    local JSON file.

    Since file operations are I/O bound, this function
    should be called in another thread.

    Parameters
    -----
    data: Dict[``str``, Any]
        A dictionary containing the snippet information
        about the track.
    """
    id = data["videoId"]
    with open(f"./tracks/{id}.json", "w") as f:
        json.dump(data, f)


class PartialInvidiousSource:
    """Represents a video object from Invidious

    This class only has information from the track and can be
    obtained from ``PartialInvidiousSource.search``
    """

    __slots__ = (
        "json",
        "api_url",
        "id",
        "title",
        "channel",
        "length",
        "description",
        "thumbnail",
    )
    if TYPE_CHECKING:
        json: Dict[str, Any]
        api_url: str
        id: str
        title: str
        channel: str
        length: int
        description: Optional[str]
        thumbnail: str

    def __init__(self, json: Dict[str, Any], api_url: str) -> None:
        self.json = json
        self.api_url = api_url
        self.id = json["videoId"]
        self.title = json["title"]
        self.channel = json["author"]
        self.length = json["lengthSeconds"]

        self.description = json.get("description")

        for image in json["videoThumbnails"]:
            self.thumbnail = image["url"]
            if "maxres" in image["quality"]:
                break

    def create_embed(self) -> discord.Embed:
        """Make a ``discord.Embed`` that represents
        basic information of the video.

        The embed is created with a title, description,
        thumbnails, and 3 fields.

        Returns
        -----
        ``discord.Embed``
            The embed with information about the video
        """
        title = escape(self.title)
        url = f"https://www.youtube.com/watch?v={self.id}"
        if self.description is not None:
            description = escape(self.description.replace("\n\n", "\n"))
            if len(description) > 300:
                description = description[:300] + f" [...]({url})"
        else:
            description = None

        embed = discord.Embed(title=title, description=description, url=url)
        embed.add_field(
            name="Channel",
            value=escape(self.channel),
            inline=False,
        )
        embed.add_field(
            name="Length",
            value=format(self.length),
        )

        if not self.thumbnail.startswith("http"):
            embed.set_thumbnail(url=self.api_url + self.thumbnail)
        else:
            embed.set_thumbnail(url=self.thumbnail)

        return embed

    @classmethod
    async def search(cls: Type[PartialInvidiousSource], query: str, *, max_results: int = 6, client: AudioClient) -> List[PartialInvidiousSource]:
        """This function is a coroutine

        Search for a list of Invidious video from a query.

        Parameters
        -----
        query: ``str``
            The searching query
        max_results: ``int``
            The maximum number of results to return
        client: ``AudioClient``
            The client to perform the request

        Returns
        -----
        List[``PartialInvidiousSource``]
            The list of searching results
        """
        params = {
            "q": query,
            "page": 0,
            "type": "video",
        }
        items = []

        for url in INVIDIOUS_URLS:
            with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
                async with client.session.get(f"{url}/api/v1/search", params=params, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        json = await response.json(encoding="utf-8")
                        items.extend(cls(data, url) for data in json[:max_results])
                        return items

        return items

    @classmethod
    async def build(cls: Type[PartialInvidiousSource], id: str, *, client: AudioClient) -> Optional[PartialInvidiousSource]:
        """This function is a coroutine

        Build a ``PartialInvidiousSource`` from a given ``id``.

        If data about a track with this ID is found in the disk
        then that data will be used, otherwise a new data will be
        fetched and written to the disk.

        Parameters
        -----
        id: ``str``
            The track ID
        client: ``AudioClient``
            The client to perform the request

        Returns
        -----
        Optional[``PartialInvidiousSource``]
            The track with the given ID, or ``None`` if not found.
        """
        data = await asyncio.to_thread(get_from_memory, id)
        if data is not None:
            return cls(data, data["api_url"])

        track = await InvidiousSource.build(id, client=client)
        if track:
            js = track.json
            return cls(js, track.api_url)


class InvidiousSource(PartialInvidiousSource):
    """Represents a playable video object from Invidious

    This class inherits from ``PartialInvidiousSource``,
    but provides additional attributes and methods that
    support music playing.

    If users want to get the Invidious URL to the audio,
    they should also use this class.
    """

    __slots__ = ("part", "left", "playable", "source")
    if TYPE_CHECKING:
        playable: bool
        source: Optional[str]

    def __init__(self, *args, **kwargs) -> None:
        self.playable = False
        self.source = None
        super().__init__(*args, **kwargs)

        for adaptiveFormat in self.json["adaptiveFormats"]:
            if adaptiveFormat.get("encoding") == "opus":
                self.source = adaptiveFormat["url"]
                break

    def initialize(self) -> None:
        """Initialize this track before playing

        This method will be automatically called
        when the first portion of the track starts
        loading. However, users can also call this
        method manually.
        """
        self.part = 0
        self.left = copy.copy(self.length)
        self.playable = True

    def fetch(self) -> Optional[discord.FFmpegOpusAudio]:
        """Fetch a 30-second portion of the audio

        If the track hasn't been initialized for
        playing yet, this will automatically call
        ``initialize()``

        Because this method is blocking, it should
        be ran in another thread.

        Returns
        -----
        Optional[``discord.FFmpegOpusAudio``]
            A playable audio source for 30 seconds,
            or ``None`` if the audio was finished.
        """

        if not self.playable:
            self.initialize()

        if self.left <= 0:
            return

        before = (
            "-start_at_zero",
            "-copyts",
            "-ss", str(30 * self.part),
            "-t", "30",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "1",
        )

        before_options = shlex.join(before)
        options = "-vn",

        # This may result in race conditions
        # so there must be only one thread
        # fetching at a time.
        self.part += 1
        self.left -= 30

        return discord.FFmpegOpusAudio(
            self.source,
            before_options=before_options,
            options=options,
        )

    async def ensure_source(self, *, client: AudioClient) -> Optional[str]:
        """This function is a coroutine

        Ensure that the opus encoded audio URL can function
        properly. If it does not then a new URL will be
        fetched via ``get_source``.

        Parameters
        -----
        client: ``AudioClient``
            The client to perform the request

        Returns
        -----
        Optional[``str``]
            The URL to the audio. This is the same as the
            ``source`` attribute of the object.
        """
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            if self.source:
                async with client.session.get(self.source, timeout=TIMEOUT) as response:
                    if response.ok:
                        return self.source

        self.source = await self.get_source()
        return self.source

    async def get_source(self, *, client: AudioClient, ignore_error: bool = False) -> Optional[str]:
        """This function is a coroutine

        Get the audio URL of the source. This method launches
        an asynchronous subprocess to ``youtube-dl``.

        Parameters
        -----
        ignore_error: ``bool``
            Whether to ignore errors from stderr
        client: ``AudioClient``
            The client to perform the request

        Returns
        -----
        Optional[``str``]
            The fetched URL, or ``None`` if an error occured.
        """
        args = (
            "youtube-dl",
            "--get-url",
            "--extract-audio",
            "--audio-format", "opus",
            "--rm-cache-dir",
            "--force-ipv4",
            f"https://www.youtube.com/watch?v={self.id}",
        )

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        __stdout, __stderr = await process.communicate()
        # These strings may be empty
        stdout = __stdout.decode("utf-8").strip("\n")
        stderr = __stderr.decode("utf-8").strip("\n")

        if not stdout and not ignore_error:
            client.bot.log(f"youtube-dl cannot fetch source for track ID {self.id}:\n{stderr}")
            await client.bot.report(f"Cannot fetch source for track `{self.id}`", send_state=False)
            return

        return stdout

    def __repr__(self) -> str:
        return f"<InvidiousSource title={self.title} id={self.id} source={self.source}>"

    @classmethod
    async def build(cls: Type[InvidiousSource], id: str, *, client: AudioClient) -> Optional[InvidiousSource]:
        """This function is a coroutine

        Build an ``InvidiousSource`` from a track ID.

        Parameters
        -----
        id: ``str``
            The track ID.
        client: ``AudioClient``
            The client to perform the request

        Returns
        -----
        Optional[``InvidiousSource``]
            The track object with the given ID.
        """
        for url in INVIDIOUS_URLS:
            with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
                async with client.session.get(f"{url}/api/v1/videos/{id}", timeout=TIMEOUT) as response:
                    if response.status == 200:
                        js = await response.json(encoding="utf-8")
                        js["api_url"] = url
                        await asyncio.to_thread(save_to_memory, js)
                        return cls(js, url)
