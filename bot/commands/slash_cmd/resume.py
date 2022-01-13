import discord

import slash
from core import bot


json = {
    "name": "resume",
    "type": 1,
    "description": "Resume the paused audio",
}


@bot.slash(json)
@slash.guild_only()
async def _resume_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player:
        await player.operable.wait()
        if player.is_paused():
            player.resume()
            return await interaction.followup.send("Resumed audio.")

    await interaction.followup.send("No audio is currently being paused to resume.")
