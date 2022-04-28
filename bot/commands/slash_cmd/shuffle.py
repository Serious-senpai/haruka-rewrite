from discord import app_commands

from _types import Interaction
from core import bot


@bot.slash(
    name="shuffle",
    description="Enable/Disable music playing shuffle",
    verified_client=False,
)
@app_commands.guild_only()
async def _shuffle_slash(interaction: Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if not player:
        return await interaction.followup.send("No audio client detected in this server.")

    if await player.switch_shuffle():
        await interaction.followup.send("Shuffle has been turned on. Songs will be played randomly.")
    else:
        await interaction.followup.send("Shuffle has been turned off. Songs will be played with the queue order.")
