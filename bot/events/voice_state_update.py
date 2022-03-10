import contextlib

import discord

from _types import Guild, Member
from core import bot


def _is_alone_in(guild: Guild) -> bool:
    if not guild.voice_client:
        return False

    return len(guild.voice_client.channel.members) == 1


@bot.event
async def on_voice_state_update(member: Member, before: discord.VoiceState, after: discord.VoiceState):
    guild = member.guild
    if _is_alone_in(guild):
        voice_client = guild.voice_client
        voice_client.pause()
        with contextlib.suppress(discord.HTTPException):
            await voice_client.target.send(f"All members have left <#{voice_client.channel.id}>. Paused audio.")
