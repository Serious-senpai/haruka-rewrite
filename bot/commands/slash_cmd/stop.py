import slash
from _types import Interaction
from core import bot


json = {
    "name": "stop",
    "type": 1,
    "description": "Stop the playing audio and disconnect from the voice channel",
}


@bot.slash(json)
@slash.guild_only()
async def _stop_slash(interaction: Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player and player.is_connected():
        await player.disconnect(force=True)
        await interaction.followup.send("Stopped player.")
    else:
        await interaction.followup.send("No currently connected player.")
