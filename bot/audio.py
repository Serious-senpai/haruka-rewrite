from __future__ import annotations

import asyncio
import contextlib
import copy
import json
import os
import random
import shlex
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, TYPE_CHECKING

import aiohttp
import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import emoji_ui
import env
import utils
from core import bot


T = TypeVar("T")
TIMEOUT = aiohttp.ClientTimeout(total=15)
HOST = env.get_host()


def in_voice() -> Callable[[T], T]:
    async def predicate(ctx: commands.Context) -> bool:
        if not getattr(ctx.author, "voice", None):
            await ctx.send("Please join a voice channel first.")
            return False

        return True
    return commands.check(predicate)


with open("./bot/assets/misc/iv_instances.txt", "r", encoding="utf-8") as f:
    INVIDIOUS_URLS = ["https://" + instance.strip("\n") for instance in f.readlines()]


if not os.path.exists("./tracks"):
    os.mkdir("./tracks")


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
        "_api_url",
        "id",
        "title",
        "channel",
        "length",
        "description",
        "thumbnail",
    )
    if TYPE_CHECKING:
        json: Dict[str, Any]
        _api_url: str
        id: str
        title: str
        channel: str
        length: int
        description: Optional[str]
        thumbnail: str

    def __init__(self, json: Dict[str, Any], api_url: str) -> None:
        self.json = json
        self._api_url = api_url
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
            description = discord.Embed.Empty

        embed = discord.Embed(title=title, description=description, url=url)
        embed.add_field(
            name="Channel",
            value=escape(self.channel),
            inline=False,
        )
        embed.add_field(
            name="Length",
            value=utils.format(self.length),
        )

        if not self.thumbnail.startswith("http"):
            embed.set_thumbnail(url=self._api_url + self.thumbnail)
        else:
            embed.set_thumbnail(url=self.thumbnail)

        return embed

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
        query: ``str``
            The searching query
        max_results: ``int``
            The maximum number of results to return

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
            with contextlib.suppress(aiohttp.ClientError):
                async with bot.session.get(f"{url}/api/v1/search", params=params, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        json = await response.json(encoding="utf-8")
                        items.extend(cls(data, url) for data in json[:max_results])
                        return items

        return items

    @classmethod
    async def build(cls: Type[PartialInvidiousSource], id: str) -> Optional[PartialInvidiousSource]:
        """This function is a coroutine

        Build a ``PartialInvidiousSource`` from a given ``id``.

        If data about a track with this ID is found in the disk
        then that data will be used, otherwise a new data will be
        fetched and written to the disk.

        Parameters
        -----
        id: ``str``
            The track ID

        Returns
        -----
        Optional[``PartialInvidiousSource``]
            The track with the given ID, or ``None`` if not found.
        """
        data = await asyncio.to_thread(get_from_memory, id)
        if data is not None:
            return cls(data, data["api_url"])

        track = await InvidiousSource.build(id)
        if track:
            # Construct json
            js = track.json
            js["api_url"] = track._api_url
            # Save to disk
            await asyncio.to_thread(save_to_memory, js)
            return cls(js, track._api_url)


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

    async def ensure_source(self) -> Optional[str]:
        """This function is a coroutine

        Ensure that the opus encoded audio URL can function
        properly. If it does not then a new URL will be
        fetched via ``get_source``.

        Returns
        -----
        Optional[``str``]
            The URL to the audio. This is the same as the
            ``source`` attribute of the object.
        """
        with contextlib.suppress(aiohttp.ClientError):
            if self.source:
                async with bot.session.get(self.source, timeout=TIMEOUT) as response:
                    if response.ok:
                        return self.source

        self.source = await self.get_source()
        return self.source

    async def get_source(self) -> Optional[str]:
        """This function is a coroutine

        Get the audio URL of the source. This method launches
        an asynchronous subprocess to ``youtube-dl``.

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

        if not stdout:
            bot.log(f"youtube-dl cannot fetch source for track ID {self.id}:\n{stderr}")
            await bot.report(f"Cannot fetch source for track `{self.id}`", send_state=False)
            return

        return stdout

    def __repr__(self) -> str:
        return f"<InvidiousSource title={self.title} id={self.id} source={self.source}>"

    @classmethod
    async def build(cls: Type[InvidiousSource], id: str) -> Optional[InvidiousSource]:
        """This function is a coroutine

        Get an ``InvidiousSource`` from a video ID.

        Parameters
        -----
        id: ``str``
            The track ID.

        Returns
        -----
        ``InvidiousSource``
            The video object with the given ID.
        """
        for url in INVIDIOUS_URLS:
            with contextlib.suppress(aiohttp.ClientError):
                async with bot.session.get(
                    f"{url}/api/v1/videos/{id}",
                    timeout=TIMEOUT,
                ) as response:
                    if response.status == 200:
                        js = await response.json(encoding="utf-8")
                        js["api_url"] = url
                        await asyncio.to_thread(save_to_memory, js)
                        return cls(js, url)

    @classmethod
    async def search(cls: Type[InvidiousSource], *args, **kwargs) -> None:
        """This function is a coroutine

        This method should never be used. Use
        ``PartialInvidiousSource.search`` instead.
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
    query: ``str``
        The searching query
    target: ``discord.abc.Messageable``
        The interaction target channel
    user_id: ``int``
        The user ID to listen to

    Returns
    -----
    Optional[``InvidiousSource``]
        The selected track. This can be ``None`` in the
        following cases:
        - No track was found. In this case a notification
        will be sent to the user
        - The user timed out for the interaction
    """
    with utils.TimingContextManager() as measure:
        results = await PartialInvidiousSource.search(query)

    if not results:
        await target.send("No matching result was found.")
        return

    embed = discord.Embed()
    embed.set_author(
        name=f"Search results for {query}",
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text=f"Fetched results in {utils.format(measure.result)}")
    for index, result in enumerate(results):
        embed.add_field(
            name=f"{emoji_ui.CHOICES[index]} {escape(result.title)}",
            value=escape(result.channel),
            inline=False,
        )

    message = await target.send(embed=embed)
    display = emoji_ui.SelectMenu(message, len(results))
    track_index = await display.listen(user_id)

    if track_index is not None:
        return await InvidiousSource.build(results[track_index].id)


async def fetch(track: InvidiousSource) -> Optional[str]:
    """This function is a coroutine

    Download a video audio to the local machine and return its URL.

    Parameters
    -----
    track: ``InvidiousSource``
        The target track.

    Returns
    -----
    Optional[``str``]
        The URL to the audio, remember that we are hosting
        on Heroku.
    """
    if os.path.isfile(f"./server/audio/{track.id}.mp3"):
        return HOST + f"/audio/{track.id}.mp3"

    url = await track.ensure_source()
    if not url:
        return

    args = (
        "ffmpeg",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-i", url,
        "-f", "mp3",
        "-vn",
        f"./server/audio/{track.id}.mp3",
    )
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.communicate()
    return HOST + f"/audio/{track.id}.mp3"


class MusicClient(discord.VoiceClient):
    """Represents an audio client within a guild.

    This is a subclass of ``discord.VoiceClient``.

    This class provides some additional functions for
    implementing the music queue system.
    """

    if TYPE_CHECKING:
        channel: discord.VoiceChannel
        _repeat: bool
        _shuffle: bool
        _stopafter: bool
        _operable: asyncio.Event
        target: Optional[discord.abc.Messageable]

    def __init__(self, *args, **kwargs) -> None:
        self._repeat = False
        self._shuffle = False
        self._stopafter = False
        self._operable = asyncio.Event()
        self.target = None
        super().__init__(*args, **kwargs)

    @classmethod
    async def queue(cls: Type[MusicClient], channel_id: int) -> List[str]:
        """This function is a coroutine

        Get the music queue of a voice channel.

        Parameters
        -----
        channel_id: ``int``
            The voice channel ID to get the music queue.

        Returns
        -----
        List[``str``]
            The list of IDs of tracks in the voice channel,
            this list can be empty.
        """
        row = await bot.conn.fetchrow(f"SELECT * FROM youtube WHERE id = '{channel_id}';")
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
        channel_id: ``int``
            The voice channel ID.
        id: ``str``
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
        channel_id: ``int``
            The voice channel ID.
        pos: Optional[``int``]
            The position of the track to remove, indexing starts from 1. If
            this argument is not provided, a random track will be poped out.

        Returns
        -----
        Optional[``str``]
            The ID of the removed track, or ``None`` if the operation failed
        """
        queue = await cls.queue(channel_id)
        pos = pos or random.randint(1, len(queue))
        try:
            track_id = queue[pos - 1]
            if pos < 1:
                raise IndexError
        except IndexError:
            pass
        else:
            await bot.conn.execute(f"UPDATE youtube SET queue = array_cat(queue[:{pos - 1}], queue[{pos + 1}:]) WHERE id = '{channel_id}';")
            return track_id

    @property
    def channel_id(self) -> Optional[int]:
        if self.channel:
            return self.channel.id

    @property
    def guild_id(self) -> Optional[int]:
        if self.guild:
            return self.guild.id

    @property
    def operable(self) -> asyncio.Event:
        return self._operable

    # A good video for debugging: https://www.youtube.com/watch?v=U03lLvhBzOw
    async def play(self, *, target: discord.abc.Messageable) -> None:
        """This function is a coroutine

        Start playing in the connected voice channel

        Parameters
        -----
        target ``discord.abc.Messageable``
            The channel to send audio playing info.
        """
        repeat_id = None
        playing_info = None
        self.target = target

        while True:
            if self._repeat and repeat_id is not None:
                track_id = repeat_id  # Warning: not popping from the queue
            elif self._shuffle:
                track_id = await self.remove(self.channel.id)
            else:
                track_id = await self.remove(self.channel.id, pos=1)

            if not track_id:
                return await self.disconnect(force=True)

            track = await InvidiousSource.build(track_id)

            if track is None:
                embed = discord.Embed(description="Cannot fetch this track, most likely the original YouTube video was deleted.\nRemoving track and continue.")
                embed.set_author(
                    name="Warning",
                    icon_url=bot.user.avatar.url,
                )
                embed.add_field(
                    name="YouTube URL",
                    value=f"https://www.youtube.com/watch?v={track_id}",
                )
                with contextlib.suppress(discord.HTTPException):
                    await self.target.send(embed=embed)
                continue

            with contextlib.suppress(discord.HTTPException):
                async with self.target.typing():
                    embed = track.create_embed()
                    embed.set_author(
                        name=f"Playing in {self.channel}",
                        icon_url=bot.user.avatar.url,
                    )
                    embed.set_footer(text=f"Shuffle: {self._shuffle} | Repeat one: {self._repeat}")

                    if playing_info:
                        with contextlib.suppress(discord.HTTPException):
                            await playing_info.delete()

                    playing_info = await self.target.send(embed=embed)

            # Check if the URL that Invidious provided
            # us is usable
            url = await track.ensure_source()

            if not url:
                with contextlib.suppress(discord.HTTPException):
                    await self.target.send("Cannot fetch the audio for this track, removing from queue.")
                continue

            async with bot.session.get(url, timeout=TIMEOUT) as response:
                if not response.ok:
                    with contextlib.suppress(discord.HTTPException):
                        await self.target.send(f"Cannot fetch the audio for this track ({response.status}), removing from queue.")
                    continue

            repeat_id = track_id
            if not self._repeat:
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
            audios = asyncio.Queue(maxsize=1)

            # Load the first audio portion asynchronously
            audio = await asyncio.to_thread(track.fetch)
            audios.put_nowait(audio)

            self._event = asyncio.Event()
            self._event.set()

            # Check that the player was not disconnected while
            # the song is still fetching
            if not self.is_connected():
                return

            # Play the audio while loading asynchronously
            async def load() -> None:
                audio = await asyncio.to_thread(track.fetch)
                await audios.put(audio)

            t = time.perf_counter()
            seq = 1

            while not audios.empty():
                audio = await audios.get()

                if not audio:
                    break

                if track.left > 0:
                    task = asyncio.create_task(load())
                else:
                    task = None

                delta = time.perf_counter() - t
                if delta > 0.5:
                    bot.log(f"Warning: audio playing in {self.channel_id}/{self.guild_id} delayed for {1000 * delta} ms")

                self._event.clear()
                self.operable.set()  # Enable pause/resume/toggle repeat

                super().play(audio, after=self._set_event)
                self._player.name = f"Channel {self.channel_id}/{self.guild_id}/seq {seq}"

                await self._event.wait()
                self.operable.clear()  # Disable pause/resume/toggle repeat
                seq += 1
                t = time.perf_counter()

                if not self.is_connected():
                    return

                if task:
                    await task

            if not self.is_connected():
                return

            if self._stopafter:
                await self.disconnect(force=True)
                with contextlib.suppress(discord.HTTPException):
                    await self.target.send("Done playing song, disconnected due to `stopafter` request.")

                return

    def _set_event(self, exc: Optional[BaseException] = None) -> None:
        self._event.set()
        if exc is not None:
            player_name = getattr(self._player, "name", "None")
            bot.log(f"Warning: Voice client in {self.channel_id}/{self.guild_id} raised an exception (ignored in _set_event method)")
            bot.log(f"AudioPlayer instance: {self._player} (thread name {player_name})")
            bot.log("".join(traceback.format_exception(exc.__class__, exc, exc.__traceback__)))
            bot.loop.create_task(bot.report("Exception while playing audio, reporting from `_set_event` method", send_state=False))
