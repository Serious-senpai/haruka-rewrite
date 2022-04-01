from __future__ import annotations

import asyncio
import contextlib
import functools
import select
import struct
import sys
import traceback
from typing import AsyncIterator, Optional, TYPE_CHECKING

import aiohttp
import discord
from nacl import secret
from nacl.exceptions import CryptoError

from lib import emojis
from .constants import TIMEOUT
from .sources import InvidiousSource
if TYPE_CHECKING:
    import haruka
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
        target: Optional[discord.abc.Messageable]

    def __init__(self, *args, **kwargs) -> None:
        self._repeat = False
        self._shuffle = False
        self._stopafter = False
        self._operable = asyncio.Event()
        self.target = None
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

    @functools.cached_property
    def audio_client(self) -> AudioClient:
        return self.client.audio

    # A good video for debugging: https://www.youtube.com/watch?v=U03lLvhBzOw
    async def play(self, *, target: discord.abc.Messageable) -> None:  # type: ignore
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
            if not self.is_connected():
                return

            if self._repeat and repeat_id is not None:
                track_id = repeat_id  # Warning: not popping from the queue
            elif self._shuffle:
                track_id = await self.audio_client.remove(self.channel.id)
            else:
                track_id = await self.audio_client.remove(self.channel.id, pos=1)

            if not track_id:
                return await self.disconnect(force=True)

            track = await self.audio_client.build(InvidiousSource, track_id)

            if track is None:
                embed = discord.Embed(description="Cannot fetch this track, most likely the original YouTube video was deleted.\nRemoving track and continue.")
                embed.set_author(
                    name="Warning",
                    icon_url=self.client.user.avatar.url,
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
                        icon_url=self.client.user.avatar.url,
                    )
                    embed.set_footer(text=f"Shuffle: {self._shuffle} | Repeat one: {self._repeat}")

                    if playing_info:
                        with contextlib.suppress(discord.HTTPException):
                            await playing_info.delete()

                    playing_info = await self.target.send(embed=embed)

            # Check if the URL that Invidious provided
            # us is usable
            url = await track.ensure_source(client=self.audio_client)

            if not url:
                with contextlib.suppress(discord.HTTPException):
                    await self.target.send(f"{emojis.MIKUCRY} Cannot fetch the audio for track ID `{track.id}`, removing from queue.")
                continue

            try:
                async with self.client.session.get(url, timeout=TIMEOUT) as response:
                    response.raise_for_status()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                with contextlib.suppress(discord.HTTPException):
                    await self.target.send(f"{emojis.MIKUCRY} Cannot fetch the audio for track ID `{track.id}` ({response.status}), removing from queue.")
                continue

            repeat_id = track_id
            if not self._repeat:
                await self.audio_client.add(self.channel.id, track_id)

            # The playing loop for a song: divide each track
            # into 30 seconds of audio buffer, when a part
            # starts playing, the next part must start
            # loading.
            #
            # The maximum size of this asyncio.Queue must be
            # only 1 to prevent race conditions as mentioned
            # above (as well as to save memory for storing
            # buffer)
            audios: asyncio.Queue[Optional[discord.FFmpegOpusAudio]] = asyncio.Queue(maxsize=1)

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
                if track is not None:
                    audio = await asyncio.to_thread(track.fetch)
                    await audios.put(audio)

            seq = 1

            while not audios.empty():
                audio = await audios.get()

                if not audio:
                    break

                if track.left > 0:
                    task = asyncio.create_task(load())
                else:
                    task = None

                self._event.clear()
                self.operable.set()  # Enable pause/resume/toggle repeat

                super().play(audio, after=self._set_event)
                if self._player:
                    self._player.name = f"Channel {self.channel_id}/{self.guild_id}/seq {seq}"

                await self._event.wait()
                self.operable.clear()  # Disable pause/resume/toggle repeat
                seq += 1

                if not self.is_connected():
                    return

                if task is not None:
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
            self.client.log(f"WARNING: Voice client in {self.channel_id}/{self.guild_id} raised an exception (ignored in _set_event method)")
            self.client.log(f"AudioPlayer instance: {self._player} (thread name {player_name})")
            self.client.log("".join(traceback.format_exception(exc.__class__, exc, exc.__traceback__)))
            self.client.loop.create_task(self.client.report("Exception while playing audio, reporting from `_set_event` method", send_state=False))


class AudioReader(discord.VoiceClient):

    if TYPE_CHECKING:
        _listening: bool

        if sys.platform == "win32":
            loop: asyncio.ProactorEventLoop
        else:
            try:
                import uvloop
            except ImportError:
                loop: asyncio.SelectorEventLoop
            else:
                loop: uvloop.Loop

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

            decrypt_payload = getattr(self, "_decrypt_" + self.mode)
            decrypted = decrypt_payload(data)

            return self._strip_header(decrypted)

    @property
    def secret_box(self) -> secret.SecretBox:
        return secret.SecretBox(bytes(self.secret_key))

    def _decrypt_xsalsa20_poly1305(self, data: bytes) -> Optional[bytes]:
        payload = data[12:]

        nonce = bytearray(24)
        nonce[:12] = data[:12]

        with contextlib.suppress(CryptoError):
            return self.secret_box.decrypt(payload, bytes(nonce))

    def _decrypt_xsalsa20_poly1305_suffix(self, data: bytes) -> Optional[bytes]:
        payload = data[12:-24]

        nonce_size = secret.SecretBox.NONCE_SIZE
        nonce = data[-nonce_size:]

        with contextlib.suppress(CryptoError):
            return self.secret_box.decrypt(payload, nonce)

    def _decrypt_xsalsa20_poly1305_lite(self, data: bytes) -> Optional[bytes]:
        payload = data[12:-4]

        nonce = bytearray(24)
        nonce[:4] = data[-4:]

        with contextlib.suppress(CryptoError):
            return self.secret_box.decrypt(payload, bytes(nonce))

    @staticmethod
    def _strip_header(data: bytes) -> bytes:
        if data[0] == 0xBE and data[1] == 0xDE and len(data) > 4:
            _, length = struct.unpack_from(">HH", data)
            offset = 4 + length * 4
            data = data[offset:]

        return data
