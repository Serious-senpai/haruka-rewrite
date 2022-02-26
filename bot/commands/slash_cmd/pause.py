import slash
from _types import Interaction
from core import bot


json = {
    "name": "pause",
    "type": 1,
    "description": "Pause the playing audio",
}


@bot.slash(json)
@slash.guild_only()
async def _pause_slash(interaction: Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player:
        await player.operable.wait()
        if player.is_playing():
            player.pause()
            return await interaction.followup.send("Paused audio.")

    await interaction.followup.send("No audio is currently being played to pause.")
