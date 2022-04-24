from _types import Interaction
from core import bot


@bot.slash(
    name="stop",
    description="Stop the playing audio and disconnect from the voice channel",
    verified_client=False,
)
async def _stop_slash(interaction: Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be invoked in a server channel.")

    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player and player.is_connected():
        await player.disconnect(force=True)
        await interaction.followup.send("Stopped player.")
    else:
        await interaction.followup.send("No currently connected player.")
