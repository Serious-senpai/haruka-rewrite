import contextlib
from typing import List

import discord

from _types import Member, VoiceState
from core import bot


def count_nonbots(members: List[Member]) -> int:
    counter = 0
    for member in members:
        if not member.bot:
            counter += 1

    return counter


@bot.event
async def on_voice_state_update(member: Member, before: VoiceState, after: VoiceState):
    if member.bot:
        return

    current = before.channel
    if current is None:
        return

    vc = before.channel.guild.voice_client
    if vc is None or vc.channel != current:
        return

    if not after.channel == current:
        if count_nonbots(current.members) == 0:
            await vc.disconnect(force=True)
            with contextlib.suppress(discord.HTTPException):
                await vc.target.send(f"All members have left <#{current.id}>. Disconnected.")
