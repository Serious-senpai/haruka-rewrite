from _types import Interaction
from core import bot


@bot.slash(
    name="shuffle",
    description="Enable/Disable music playing shuffle",
)
async def _shuffle_slash(interaction: Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be invoked in a server channel.")

    player = interaction.guild.voice_client
    if player:
        player._shuffle = not player._shuffle
        if player._shuffle:
            await interaction.response.send_message("Shuffle has been turned on. Songs will be played randomly.")
        else:
            await interaction.response.send_message("Shuffle has been turned off. Songs will be played with the queue order.")
    else:
        await interaction.response.send_message("No audio client detected in this server.")
