import discord

import slash
from core import bot


json = {
    "name": "shuffle",
    "type": 1,
    "description": "Enable/Disable music playing shuffle",
}


@bot.slash(json)
@slash.guild_only()
async def _shuffle_slash(interaction: discord.Interaction):
    player = interaction.guild.voice_client
    if player:
        player._shuffle = not player._shuffle
        if player._shuffle:
            await interaction.response.send_message("Shuffle has been turned on. Songs will be played randomly.")
        else:
            await interaction.response.send_message("Shuffle has been turned off. Songs will be played with the queue order.")
    else:
        await interaction.response.send_message("No audio client detected in this server.")
