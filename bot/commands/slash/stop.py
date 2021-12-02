from typing import Any, Dict, Optional

import discord

from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "stop",
    "type": 1,
    "description": "Stop the playing audio and disconnect from the voice channel",
}


@bot.slash(json)
async def _stop_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    player: Optional[MusicClient] = interaction.guild.voice_client

    if player and player.is_connected():
        await player.disconnect(force = True)
        await interaction.followup.send("Stopped player.")
    else:
        await interaction.followup.send("No currently connected player.")
