from typing import Any, Dict, Optional

import discord

from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "shuffle",
    "type": 1,
    "description": "Enable/Disable music playing shuffle",
}


@bot.slash(json)
async def _shuffle_slash(interaction: discord.Interaction):
    player: Optional[MusicClient] = interaction.guild.voice_client
    if player:
        player._shuffle = not player._shuffle
        if player._shuffle:
            await interaction.response.send_message("Shuffle has been turned on. Songs will be played randomly.")
        else:
            await interaction.response.send_message("Shuffle has been turned off. Songs will be played with the queue order.")
    else:
        await interaction.response.send_message("No audio client detected in this server.")
