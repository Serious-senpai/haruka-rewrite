from typing import Any, Dict, Optional

import discord

import slash
from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "repeat",
    "type": 1,
    "description": "Switch between REPEAT_ONE and REPEAT_ALL",
}


@bot.slash(json)
@slash.guild_only()
async def _repeat_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    player: Optional[MusicClient] = interaction.guild.voice_client

    if player:
        await player._operable.wait()
        player._repeat = not player._repeat

        if player._repeat:
            await interaction.followup.send("Switched to `REPEAT ONE` mode. The current song will be play repeatedly.")
        else:
            await interaction.followup.send("Switched to `REPEAT ALL` mode. All songs will be played as normal.")

    else:
        await interaction.followup.send("No audio is currently being played.")