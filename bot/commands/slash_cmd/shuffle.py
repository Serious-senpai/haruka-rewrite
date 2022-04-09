from _types import Interaction
from core import bot


@bot.slash(
    name="shuffle",
    description="Enable/Disable music playing shuffle",
)
async def _shuffle_slash(interaction: Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be invoked in a server channel.")

    await interaction.response.defer()
    player = interaction.guild.voice_client

    if not player:
        return await interaction.followup.send("No audio client detected in this server.")

    if await player.switch_shuffle():
        await interaction.followup.send("Shuffle has been turned on. Songs will be played randomly.")
    else:
        await interaction.followup.send("Shuffle has been turned off. Songs will be played with the queue order.")
