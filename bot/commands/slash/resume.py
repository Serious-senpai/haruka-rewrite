from typing import Any, Dict, Optional

import discord

from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "resume",
    "type": 1,
    "description": "Resume the paused audio",
}


@bot.slash(json)
async def _resume_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    player: Optional[MusicClient] = interaction.guild.voice_client

    if player:
        await player._operable.wait()
        if player.is_paused():
            player.resume()
            return await interaction.followup.send("Resumed audio.")

    await interaction.followup.send("No audio is currently being paused to resume.")
