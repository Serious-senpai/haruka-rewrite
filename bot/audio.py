from __future__ import annotations

import asyncio
import copy
import json
import os
import random
import shlex
import time
import traceback
from typing import Any, Dict, List, Literal, Optional, Tuple, Type

import aiohttp
import asyncpg
import discord
from discord.utils import escape_markdown as escape

import asyncfile
import emoji_ui
from core import bot


TIMEOUT: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=15)
SIZE_LIMIT: int = 8 << 20


with open("./bot/assets/misc/iv_instances.txt", "r", encoding="utf-8") as f:
    INVIDIOUS_URLS: List[str] = ["https://" + instance.strip("\n") for instance in f.readlines()]


if not os.path.exists("./tracks"):
    os.mkdir("./tracks")


def get_from_memory(id: str) -> Optional[Dict[str, Any]]:
    """Load snippet information about a track from a
    local JSON file.

    Since file operations are I/O bound, this function
    should be called in another thread.

    Parameters
    -----
    id: :class:`str`
        The track ID.

    Returns
    -----
    Optional[Dict[:class:`str`, Any]]
        A dictionary containing the snippet information
        about the track, or ``None`` if not found.
    """
    if os.path.isfile(f"./tracks/{id}.json"):
        with open(f"./tracks/{id}.json", "r") as f:
            data: Dict[str, Any] = json.load(f)

        return data


def save_to_memory(data: Dict[str, Any]) -> None:
    """Save snippet information about a track to a
    local JSON file.

    Since file operations are I/O bound, this function
    should be called in another thread.

    Parameters
    -----
    data: Dict[:class:`str`, Any]
        A dictionary containing the snippet information
        about the track.
    """
    id: str = data["videoId"]
    with open(f"./tracks/{id}.json", "w") as f:
        json.dump(data, f)


class PartialInvidiousSource:
    """Represents a video object from Invidious

    This class only has information from the track and can be
    obtained from :meth:`PartialInvidiousSource.search`
    """

    __slots__ = (
        "_json",
        "_api_url"
    )

    def __init__(self, json: Dict[str, Any], api_url: str) -> None:
        self._json: Dict[str, Any] = json
        self._api_url: str = api_url

    @property
    def id(self) -> str:
        """The ID of the video from Invidious as well as YouTube"""
        return self._json["videoId"]

    @property
    def title(self) -> str:
        """The title of the video"""
        return self._json["title"]

    @property
    def channel(self) -> str:
        """The channel that published the video"""
        return self._json["author"]

    @property
    def description(self) -> Optional[str]:
        """The description of the video"""
        desc: Optional[str] = self._json.get("description")

        if desc:
            desc = desc.replace("\n\n", "\n")
            if len(desc) > 300:
                desc = desc[:300] + " ..."

        return desc

    @property
    def thumbnail(self) -> str:
        """The URL to the thumbnail of the video"""
        for image in self._json["videoThumbnails"]:
            if "maxres" in image["quality"]:
                return image["url"]

        return self._json["videoThumbnails"].pop()["url"]

    @property
    def length(self) -> int:
        """The length of the video"""
        return self._json["lengthSeconds"]

    def create_embed(self) -> discord.Embed:
        """Make a :class:`discord.Embed` that represents
        basic information of the video.

        The embed is created with a title, description,
        thumbnails, and 3 fields.

        Returns
        -----
        :class:`discord.Embed`
            The embed with information about the video
        """
        em: discord.Embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.description) if self.description else discord.Embed.Empty,
            url=f"https://www.youtube.com/watch?v={self.id}",
            color=0x2ECC71,
        )
        em.add_field(
            name="Channel",
            value=escape(self.channel),
            inline=False,
        )
        em.add_field(
            name="Length",
            value=f"{self.length} seconds",
        )

        if not self.thumbnail.startswith("http"):
            em.set_thumbnail(url=self._api_url + self.thumbnail)
        else:
            em.set_thumbnail(url=self.thumbnail)

        return em

    @classmethod
    async def search(
        cls: Type[PartialInvidiousSource],
        query: str,
        *,
        max_results: int = 6,
    ) -> List[PartialInvidiousSource]:
        """This function is a coroutine

        Search for a list of Invidious video from
        a query.

        Parameters
        -----
        query: :class:`str`
            The searching query
        max_results: :class:`int`
            The maximum number of results to return

        Returns
        -----
        List[:class:`PartialInvidiousSource`]
            The list of searching results
        """
        params = {
            "q": query,
            "page": 0,
            "type": "video",
        }
        items: List[PartialInvidiousSource] = []

        for url in INVIDIOUS_URLS:
            try:
                async with bot.session.get(f"{url}/api/v1/search", params=params, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        json: List[Dict[str, Any]] = await response.json()
                        items.extend(cls(data, url) for data in json[:max_results])
                        return items
            except BaseException:
                continue

        return items

    @classmethod
    async def build(cls: Type[PartialInvidiousSource], id: str) -> Optional[PartialInvidiousSource]:
        """This function is a coroutine

        Build a :class:`PartialInvidiousSource` from a given ``id``.

        If data about a track with this ID is found in the disk
        then that data will be used, otherwise a new data will be
        fetched and written to the disk.

        Parameters
        -----
        id: :class:`str`
            The track ID

        Returns
        -----
        Optional[:class:`PartialInvidiousSource`]
            The track with the given ID, or ``None`` if not found.
        """
        data: Optional[Dict[str, Any]] = await asyncio.to_thread(get_from_memory, id)
        if data is not None:
            return cls(data, data["api_url"])

        track: Optional[InvidiousSource] = await InvidiousSource.build(id)
        if track:
            # Construct json
            data: Dict[str, Any] = track._json
            data["api_url"] = track._api_url
            # Save to disk
            await asyncio.to_thread(save_to_memory, data)
            return cls(data, track._api_url)


class InvidiousSource(PartialInvidiousSource):
    """Represents a playable video object from Invidious

    This class inherits from :class:`PartialInvidiousSource`,
    but provides additional attributes and methods that
    support music playing.

    If users want to get the Invidious URL to the audio,
    they should also use this class.
    """

    __slots__ = (
        "_json",
        "_api_url",
        "part",
        "left",
        "playable",
        "source",
    )

    def __init__(self, *args, **kwargs) -> None:
        self.playable: bool = False
        self.source: Optional[str] = None
        super().__init__(*args, **kwargs)

        for adaptiveFormat in self._json["adaptiveFormats"]:
            if adaptiveFormat.get("encoding") == "opus":
                self.source = adaptiveFormat["url"]
                return

    def initialize(self) -> None:
        """Initialize this track before playing

        This method will be automatically called
        when the first portion of the track starts
        loading. However, users can also call this
        method manually.
        """
        self.part: int = 0
        self.left: int = copy.deepcopy(self.length)
        self.playable: bool = True

    def fetch(self) -> Optional[discord.FFmpegOpusAudio]:
        """Fetch a 30-second portion of the audio

        If the track hasn't been initialized for
        playing yet, this will automatically call
        :meth:`initialize()`

        Because this method is blocking, it should
        be ran in another thread.

        Returns
        -----
        Optional[:class:`discord.FFmpegOpusAudio`]
            A playable audio source for 30 seconds,
            or ``None`` if the audio was finished.
        """

        if not self.playable:
            self.initialize()

        if self.left <= 0:
            return

        before: Tuple[str, ...] = (
            "-start_at_zero",
            "-copyts",
            "-ss", str(30 * self.part),
            "-t", "30",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "1",
        )

        before_options: str = shlex.join(before)
        options: str = "-vn",

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

    async def ensure_source(self) -> Optional[str]:
        """This function is a coroutine

        Ensure that the opus encoded audio URL can function
        properly. If it does not then a new URL will be
        fetched via :meth:`get_source`.

        Returns
        -----
        Optional[:class:`str`]
            The URL to the audio. This is the same as the
            ``source`` attribute of the object.
        """
        if self.source:
            async with bot.session.get(self.source, timeout=TIMEOUT) as response:
                if response.ok:
                    return self.source

        self.source = await self.get_source()
        return self.source

    async def get_source(self) -> Optional[str]:
        """This function is a coroutine

        Get the video/audio URL of the source. This method
        launches an asynchronous subprocess to ``youtube-dl``.

        Parameters
        -----
        format: Literal[``video``, ``audio``]
            Whether a video or an audio URL should be returned.

        Returns
        -----
        Optional[:class:`str`]
            The fetched URL, or ``None`` if an error occured.
        """
        args: List[str] = [
            "youtube-dl",
            "--get-url",
            "--extract-audio",
            "--audio-format", "opus",
            "--rm-cache-dir",
            "--force-ipv4",
            f"https://www.youtube.com/watch?v={self.id}",
        ]

        process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await process.communicate()
            url: Optional[str] = stdout.decode("utf-8").split("\n")[0]
        except BaseException:
            bot.log(f"Error while getting URL for track {self.id}.")
            bot.log(traceback.format_exc())
            bot.log("stdout from youtube-dl:" + stdout.decode("utf-8"))
            bot.log("stderr from youtube-dl:" + stderr.decode("utf-8"))
            url: Optional[str] = None

        return url

    @classmethod
    async def build(cls: Type[InvidiousSource], id: str) -> Optional[InvidiousSource]:
        """This function is a coroutine

        Get a :class:`InvidiousSource` from a video ID.

        Parameters
        -----
        id: :class:`str`
            The track ID.

        Returns
        -----
        :class:`InvidiousSource`
            The video object with the given ID.
        """
        for url in INVIDIOUS_URLS:
            try:
                async with bot.session.get(
                    f"{url}/api/v1/videos/{id}",
                    timeout=TIMEOUT,
                ) as response:
                    if response.ok:
                        json: Dict[str, Any] = await response.json()
                        await asyncio.to_thread(
                            save_to_memory,
                            json | {"api_url": url},
                        )
                        return cls(json, url)
            except BaseException:
                continue

    @classmethod
    async def search(cls: Type[InvidiousSource], *args, **kwargs) -> None:
        """This function is a coroutine

        This method should never be used. Use
        :meth:`PartialInvidiousSource.search` instead.
        """
        raise NotImplementedError


async def embed_search(
    query: str,
    target: discord.abc.Messageable,
    user_id: int,
) -> Optional[InvidiousSource]:
    """This function is a coroutine

    Let a user with ``user_id`` search for a YouTube track
    via an embed.

    Parameters
    -----
    query: :class:`str`
        The searching query
    target: :class:`discord.abc.Messageable`
        The interaction target channel
    user_id: :class:`int`
        The user ID to listen to

    Returns
    -----
    Optional[:class:`InvidiousSource`]
        The selected track. This can be ``None`` in the
        following cases:
        - No track was found. In this case a notification
        will be sent to the user
        - The user timed out for the interaction
    """
    t: float = time.perf_counter()
    results: List[PartialInvidiousSource] = await PartialInvidiousSource.search(query)
    done: float = time.perf_counter() - t

    if not results:
        await target.send("No matching result was found.")
        return

    embed: discord.Embed = discord.Embed(
        color=0x2ECC71,
    )
    embed.set_author(
        name=f"Search results for {query}",
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text="Fetched results in {:.2f} ms".format(1000 * done))
    for index, result in enumerate(results):
        embed.add_field(
            name=f"{emoji_ui.CHOICES[index]} {escape(result.title)}",
            value=escape(result.channel),
            inline=False,
        )

    message: discord.Message = await target.send(embed=embed)
    display: emoji_ui.SelectMenu = emoji_ui.SelectMenu(message, len(results))
    track_index: Optional[int] = await display.listen(user_id)

    if track_index is not None:
        return await InvidiousSource.build(results[track_index].id)


async def fetch(track_id: str) -> Optional[str]:
    """This function is a coroutine

    Download a video to the local machine and return its URL.

    Parameters
    -----
    track_id: :class:`str`
        The YouTube track ID

    Returns
    -----
    Optional[:class:`str`]
        The URL to the video, remember that we are hosting
        on Heroku.
    """
    if os.path.isfile(f"./server/video/{track_id}.mp4"):
        return bot.host + f"/video/{track_id}.mp4"

    process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
        "youtube-dl",
        "--format", "mp4",
        "--http-chunk-size", "10485760",
        "--rm-cache-dir",
        "--force-ipv4",
        f"https://www.youtube.com/watch?v={track_id}",
        "-o", f"./server/video/{track_id}.mp4",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if stderr:
        bot.log(f"Warning while fetching track ID {track_id}:")
        bot.log(stderr.decode("utf-8"))
    else:
        return bot.host + f"/video/{track_id}.mp4"


class MusicClient(discord.VoiceClient):
    """Represents an audio client within a guild.

    This is a subclass of :class:`discord.VoiceClient`.

    This class provides some additional functions for
    implementing the music queue system.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._shuffle: bool = False
        self._stopafter: bool = False
        self._operable: asyncio.Event = asyncio.Event()
        self.target: Optional[discord.abc.Messageable] = None
        super().__init__(*args, **kwargs)

    @classmethod
    async def queue(cls: Type[MusicClient], channel_id: int) -> List[str]:
        """This function is a coroutine

        Get the music queue of a voice channel.

        Parameters
        -----
        channel_id: :class:`int`
            The voice channel ID to get the music queue.

        Returns
        -----
        List[:class:`str`]
            The list of IDs of tracks in the voice channel,
            this list can be empty.
        """
        row: Optional[asyncpg.Record] = await bot.conn.fetchrow(f"SELECT * FROM youtube WHERE id = '{channel_id}';")
        if not row:
            await bot.conn.execute(f"INSERT INTO youtube VALUES ('{channel_id}', $1);", [])
            track_ids = []
        else:
            track_ids = row["queue"]
        return track_ids

    @classmethod
    async def add(cls: Type[MusicClient], channel_id: int, id: str) -> None:
        """This function is a coroutine

        Add a track to the music queue of a voice channel.

        Parameters
        -----
        channel_id: :class:`int`
            The voice channel ID.
        id: :class:`str`
            The ID of the track to add, in this case, a YouTube video
        """
        await bot.conn.execute(f"UPDATE youtube SET queue = array_append(queue, '{id}') WHERE id = '{channel_id}';")

    @classmethod
    async def remove(
        cls: Type[MusicClient],
        channel_id: int,
        *,
        pos: Optional[int] = None,
    ) -> Optional[str]:
        """This function is a coroutine

        Remove a track from the music queue of a voice channel.

        Parameters
        -----
        channel_id: :class:`int`
            The voice channel ID.
        pos: Optional[:class:`int`]
            The position of the track to remove, indexing starts from 1. If
            this argument is not provided, a random track will be poped out.

        Returns
        -----
        Optional[:class:`str`]
            The ID of the removed track, or ``None`` if the operation failed
        """
        queue: List[str] = await cls.queue(channel_id)
        pos: int = pos or random.randint(1, len(queue))
        try:
            track_id: str = queue[pos - 1]
            if pos < 1:
                raise IndexError
        except IndexError:
            pass
        else:
            await bot.conn.execute(f"UPDATE youtube SET queue = array_cat(queue[:{pos - 1}], queue[{pos + 1}:]) WHERE id = '{channel_id}';")
            return track_id

    # A good video for debugging: https://www.youtube.com/watch?v=U03lLvhBzOw
    async def play(self, *, target: discord.abc.Messageable) -> None:
        """This function is a coroutine

        Start playing in the connected voice channel

        Parameters
        -----
        target :class:`discord.abc.Messageable`
            The channel to send audio playing info.
        """
        playing_info: Optional[discord.Message] = None
        self.target = target
        while True:
            if self._shuffle:
                track_id: Optional[str] = await self.remove(self.channel.id)
            else:
                track_id: Optional[str] = await self.remove(self.channel.id, pos=1)

            if not track_id:
                return await self.disconnect(force=True)

            track: Optional[InvidiousSource] = await InvidiousSource.build(track_id)

            if track is None:
                em: discord.Embed = discord.Embed(
                    description="Cannot fetch this track, most likely the original YouTube video was deleted.\nRemoving track and continue.",
                    color=0x2ECC71,
                )
                em.set_author(
                    name="Warning",
                    icon_url=bot.user.avatar.url,
                )
                em.add_field(
                    name="YouTube URL",
                    value=f"https://www.youtube.com/watch?v={track_id}",
                )
                try:
                    await self.target.send(embed=em)
                except discord.Forbidden:
                    pass
                continue

            try:
                async with self.target.typing():
                    em: discord.Embed = track.create_embed()
                    em.set_author(
                        name=f"Playing in {self.channel}",
                        icon_url=bot.user.avatar.url,
                    )

                    if self._shuffle:
                        em.set_footer(text="Shuffle is ON")
                    else:
                        em.set_footer(text="Shuffle is OFF")

                    if playing_info:
                        try:
                            await playing_info.delete()
                        except discord.HTTPException:
                            pass

                    playing_info = await self.target.send(embed=em)
            except discord.Forbidden:
                pass

            # Check if the URL that Invidious provided
            # us is usable
            url: Optional[str] = await track.ensure_source()

            if not url:
                try:
                    await self.target.send("Cannot fetch the audio for this track, removing from queue.")
                except discord.Forbidden:
                    pass
                continue

            async with bot.session.get(url, timeout=TIMEOUT) as response:
                if not response.ok:
                    try:
                        await self.target.send(f"Cannot fetch the audio for this track ({response.status}), removing from queue.")
                    except discord.Forbidden:
                        pass
                    continue

            await self.add(self.channel.id, track_id)

            # The playing loop for a song: divide each track
            # into 30 seconds of audio buffer, when a part
            # starts playing, the next part must start
            # loading.
            #
            # The maximum size of this asyncio.Queue must be
            # only 1 to prevent race conditions as mentioned
            # above (as well as to save memory for storing
            # buffer)
            audios: asyncio.Queue = asyncio.Queue(maxsize=1)

            # Load the first audio portion asynchronously
            audio: discord.FFmpegOpusAudio = await asyncio.to_thread(track.fetch)
            audios.put_nowait(audio)

            self._event: asyncio.Event = asyncio.Event()
            self._event.set()

            # Check that the player was not disconnected while
            # the song is still fetching
            if not self.is_connected():
                return

            # Play the audio while loading asynchronously
            async def load() -> None:
                audio: Optional[discord.FFmpegOpusAudio] = await asyncio.to_thread(track.fetch)
                await audios.put(audio)

            task: Optional[asyncio.Task]
            t: float = time.perf_counter()
            while not audios.empty():
                audio: Optional[discord.FFmpegOpusAudio] = await audios.get()

                if not audio:
                    break

                if track.left > 0:
                    task = asyncio.create_task(load())
                else:
                    task = None

                delta: float = time.perf_counter() - t
                if delta > 0.5:
                    bot.log(f"Warning: audio playing in {self.channel.name}/{self.guild.name} delayed for {1000 * delta} ms")

                self._event.clear()
                self._operable.set()  # Enable pause/resume

                super().play(audio, after=self._set_event)

                await self._event.wait()
                self._operable.clear()  # Disable pause/resume
                t = time.perf_counter()

                if not self.is_connected():
                    return

                if task:
                    await task

            if not self.is_connected():
                return

            if self._stopafter:
                await self.disconnect(force=True)
                try:
                    await self.target.send("Done playing song, disconnected due to `stopafter` request.")
                except discord.Forbidden:
                    pass
                return

    def _set_event(self, *args, **kwargs) -> None:
        self._event.set()
