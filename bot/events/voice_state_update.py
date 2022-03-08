import contextlib

import discord

from _types import Member
from audio import MusicClient
from core import bot


def _is_alone_in(voice_client: MusicClient) -> bool:
    member = voice_client.guild.me
    if not member.voice:
        return False

    return len(voice_client.channel.members) == 1


@bot.event
async def on_voice_state_update(member: Member, before: discord.VoiceState, after: discord.VoiceState):
    guild = member.guild
    if guild.voice_client is None:
        return

    voice_client = guild.voice_client
    if _is_alone_in(voice_client):
        voice_client.pause()
        with contextlib.suppress(discord.HTTPException):
            await voice_client.target.send(f"All members have left <#{voice_client.channel.id}>. Paused audio.")
