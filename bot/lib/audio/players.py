from __future__ import annotations

import asyncio
import contextlib
import functools
import select
import time
import traceback
from typing import Any, AsyncIterator, Coroutine, Optional, TYPE_CHECKING

import discord

from lib import emojis
from .sources import InvidiousSource
if TYPE_CHECKING:
    import haruka
    from _types import Loop
    from .client import AudioClient


__all__ = ("MusicClient",)


class MusicClient(discord.VoiceClient):
    """Represents an audio client within a guild.

    This is a subclass of ``discord.VoiceClient``.

    This class provides some additional functions for
    implementing the music queue system.
    """

    if TYPE_CHECKING:
        client: haruka.Haruka
        channel: discord.VoiceChannel
        _repeat: bool
        _shuffle: bool
        _stopafter: bool
        _operable: asyncio.Event
        _event: asyncio.Event
        target: discord.abc.Messageable
        current_track: InvidiousSource
        player: asyncio.Task[None]
        _debug_audio_length: bool

    def __init__(self, *args, **kwargs) -> None:
        self._repeat = False
        self._shuffle = False
        self._stopafter = False
        self._operable = asyncio.Event()
        self._event = asyncio.Event()
        self._debug_audio_length = False
        super().__init__(*args, **kwargs)

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

    @property
    def repeat(self) -> bool:
        """Whether this player is set to REPEAT_ONE mode"""
        return self._repeat

    @property
    def shuffle(self) -> bool:
        """Whether this player's SHUFFLE mode is turned on"""
        return self._shuffle

    @property
    def stopafter(self) -> bool:
        """Whether this player's STOPAFTER mode is turned on"""
        return self._stopafter

    async def switch_repeat(self) -> bool:
        await self.operable.wait()
        self._repeat = not self._repeat
        return self._repeat

    async def switch_shuffle(self) -> bool:
        await self.operable.wait()
        self._shuffle = not self._shuffle
        return self._shuffle

    async def switch_stopafter(self) -> bool:
        await self.operable.wait()
        self._stopafter = not self._stopafter
        return self._stopafter

    @functools.cached_property
    def audio_client(self) -> AudioClient:
        return self.client.audio

    async def notify(self, *args, **kwargs) -> Optional[discord.Message]:
        """This function is a coroutine

        Send a message to the notify channel. The arguments and keyword
        arguments are similar to ``discord.abc.Messageable.send()``

        Returns
        -----
        Optional[``discord.Message``]
            The created message, or ``None`` if the process failed.
        """
        with contextlib.suppress(discord.HTTPException):
            return await self.target.send(*args, **kwargs)

    async def when_complete(self, coro: Coroutine[Any, Any, Any]) -> None:
        """This function is a coroutine

        Assign a coroutine to be run when the current track completes
        playing.

        Parameters
        -----
        coro: ``Coroutine[Any, Any, Any]``
            The coroutine to be run
        """
        await self._operable.wait()
        self.player.add_done_callback(lambda _: asyncio.create_task(coro))

    async def skip(self) -> None:
        """This function is a coroutine

        Skip the current track and start the new one.
        The next track will be the one at the first index in the queue
        if shuffle is off and a random one if shuffle is on.

        This method will block until we finishes playing.
        """
        await self._operable.wait()
        self._operable.clear()
        self.stop()
        self.player.cancel()
        await self.play(target=self.target)

    async def play(self, *, target: discord.abc.Messageable) -> None:
        """This function is a coroutine

        Start playing music in the connected voice channel.
        This method will block until we finishes playing.

        Parameters
        -----
        target ``discord.abc.Messageable``
            The channel to send audio playing info.
        """
        self.target = target
        track_id = None

        while self.is_connected():
            if not self._repeat or track_id is None:
                add_back = True
                track_id = await self.audio_client.remove(self.channel.id, pos=None if self._shuffle else 1)
                if track_id is None:
                    await self.notify("This voice channel's music queue is currently empty!")
                    await self.disconnect(force=True)
                    return

            else:
                add_back = False

            track = await InvidiousSource.build(track_id, client=self.audio_client)
            if track is None or not await track.ensure_source(client=self.audio_client):
                await self.notify(f"{emojis.MIKUCRY} Cannot fetch audio for track ID `{track_id}` (https://www.youtube.com/watch?v={track_id}), removing from the queue.")
                continue

            if add_back:
                await self.audio_client.add(self.channel.id, track_id)

            self.player = asyncio.create_task(self._play(track))

            try:
                await self.player
            except asyncio.CancelledError:
                return

            if self._stopafter:
                await self.notify("Done playing song, disconnected due to `stopafter` request.")
                await self.disconnect(force=True)
                return

    # A good video for debugging: https://www.youtube.com/watch?v=U03lLvhBzOw
    async def _play(self, track: InvidiousSource) -> None:
        """This function is a coroutine

        Play the given track in the connected voice channel

        Parameters
        -----
        track: ``InvidiousSource``
            The track to be played
        """
        self.current_track = track
        buffer: asyncio.Queue[discord.FFmpegOpusAudio] = asyncio.Queue(maxsize=1)
        buffer.put_nowait(await asyncio.to_thread(track.fetch))

        with contextlib.suppress(discord.HTTPException):
            async with self.target.typing():
                embed = track.create_embed()
                embed.set_author(
                    name=f"Playing in {self.channel}",
                    icon_url=self.client.user.avatar.url,
                )
                embed.set_footer(text=f"Shuffle: {self.shuffle} | Repeat one: {self.repeat}")

                await self.notify(embed=embed)

        async def load(
            buffer: asyncio.Queue[discord.FFmpegOpusAudio],
            track: InvidiousSource,
        ) -> None:
            audio = await asyncio.to_thread(track.fetch)
            if audio is not None:
                await buffer.put(audio)

        if self._debug_audio_length:
            await self.notify("Debugging audio length")
            _start_timestamp = time.perf_counter()

        while not buffer.empty() and self.is_connected():
            task = asyncio.create_task(load(buffer, track))

            self._event.clear()
            self._operable.set()

            super().play(buffer.get_nowait(), after=self._set_event)

            await self._event.wait()
            self._operable.clear()

            await task

        if self._debug_audio_length:
            _duration = time.perf_counter() - _start_timestamp
            await self.notify(f"Track ID {track.id} played for {_duration:.2f}s/{track.length}s.\nSource: `{track.source_api}`")

    def _set_event(self, exc: Optional[BaseException] = None) -> None:
        self._event.set()
        if exc is not None:
            if isinstance(exc, OSError):
                return

            player_name = getattr(self._player, "name", "None")
            self.client.log(f"WARNING: Voice client in {self.channel_id}/{self.guild_id} raised an exception (ignored in _set_event method)")
            self.client.log(f"AudioPlayer instance: {self._player} (thread name {player_name})")
            self.client.log("".join(traceback.format_exception(exc.__class__, exc, exc.__traceback__)))
            self.client.loop.create_task(self.client.report("Exception while playing audio, reporting from `_set_event` method", send_state=False))


class AudioReader(discord.VoiceClient):

    if TYPE_CHECKING:
        _listening: bool
        loop: Loop

    def __init__(self, *args, **kwargs) -> None:
        self._listening = False
        super().__init__(*args, **kwargs)

    @property
    def listening(self) -> bool:
        return self._listening

    async def receive(self) -> AsyncIterator[bytes]:
        if self._listening:
            raise RuntimeError("This audio stream has already been listened to")

        self._listening = True
        while self.is_connected():
            data = await asyncio.to_thread(self._do_receive)
            if data is not None:
                yield data

        self._listening = False

    def _do_receive(self) -> Optional[bytes]:
        socket = self.socket
        rsock, _, _ = select.select([socket], [], [socket], 0.1)
        if rsock:
            try:
                data = socket.recv(4096)
            except OSError:
                return

            return data
