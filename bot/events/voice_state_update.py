import asyncio
import contextlib
from typing import Optional

import discord

from audio import MusicClient
from core import bot


def _is_alone_in(voice_client: MusicClient) -> bool:
    return len(voice_client.channel.members) == 1


def _check_resume(voice_client: MusicClient) -> None:
    if voice_client.is_paused():
        voice_client.resume()


async def prepare_disconnect(voice_client: Optional[MusicClient]) -> None:
    try:
        # Check if someone has joined the channel within this 5-minute period
        await bot.wait_for(
            "voice_state_update",
            check=lambda member, before, after: after.channel == voice_client.channel,
            timeout=300.0,
        )
    except AttributeError:
        # We have been disconnected (voice_client = None)
        return
    except asyncio.TimeoutError:
        # No one has joined, proceed further, or...
        pass
    else:
        # ... someone has joined, resume the paused audio (if it is paused) and exit the coroutine
        _check_resume(voice_client)
        return

    if _is_alone_in(voice_client):
        await voice_client.disconnect(force=True)
        with contextlib.suppress(discord.HTTPException):
            await voice_client.target.send(f"<#{voice_client.channel.id}> has been idle for 5 minutes. Disconnected.")


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if not member.bot:
        voice_client: Optional[MusicClient] = member.guild.voice_client

        if voice_client and _is_alone_in(voice_client):
            if voice_client.is_playing():
                await voice_client.operable.wait()
                voice_client.pause()
                with contextlib.suppress(discord.HTTPException):
                    await voice_client.target.send(f"All members have left <#{voice_client.channel.id}>. Paused audio.")

            bot.loop.create_task(prepare_disconnect(voice_client))
