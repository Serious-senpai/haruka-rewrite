from typing import Any, Dict, Optional

import discord

import slash
from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "pause",
    "type": 1,
    "description": "Pause the playing audio",
}


@bot.slash(json)
@slash.guild_only()
async def _pause_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    player: Optional[MusicClient] = interaction.guild.voice_client

    if player:
        await player._operable.wait()
        if player.is_playing():
            player.pause()
            return await interaction.followup.send("Paused audio.")

    await interaction.followup.send("No audio is currently being played to pause.")
