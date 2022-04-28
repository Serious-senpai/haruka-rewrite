from discord import app_commands

from _types import Interaction
from core import bot


@bot.slash(
    name="resume",
    description="Resume the paused audio",
    verified_client=False,
)
@app_commands.guild_only()
async def _resume_slash(interaction: Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player:
        await player.operable.wait()
        if player.is_paused():
            player.resume()
            return await interaction.followup.send("Resumed audio.")

    await interaction.followup.send("No audio is currently being paused to resume.")
