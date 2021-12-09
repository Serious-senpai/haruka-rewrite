from typing import Any, Dict, Optional

import discord

import slash
from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "stopafter",
    "type": 1,
    "description": "Tell the bot to disconnect after playing the current song",
}


@bot.slash(json)
@slash.guild_only()
async def _stopafter_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    player: Optional[MusicClient] = interaction.guild.voice_client

    if not player:
        return await interaction.followup.send("No currently connected player.")

    player._stopafter = not player._stopafter
    if player._stopafter:
        await interaction.followup.send("Enabled `stopafter`. This will be the last song to be played.")
    else:
        await interaction.followup.send("Disabled `stopafter`. Other songs will be played normally after this one ends.")
