import contextlib

import discord

import audio
from _types import Member
from core import bot


@bot.event
async def on_voice_state_update(member: Member, before: discord.VoiceState, after: discord.VoiceState):
    guild = member.guild
    vc = guild.voice_client

    if not vc or not vc.is_connected():
        return

    if isinstance(vc, audio.MusicClient):
        if len(vc.channel.members) == 1:
            vc.pause()
            with contextlib.suppress(discord.HTTPException):
                await vc.target.send(f"All members have left <#{vc.channel.id}>. Paused audio.")
