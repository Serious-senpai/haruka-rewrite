from _types import Interaction
from core import bot


@bot.slash(
    name="pause",
    description="Pause the playing audio",
    verified_client=False,
)
async def _pause_slash(interaction: Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be invoked in a server channel.")

    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player:
        await player.operable.wait()
        if player.is_playing():
            player.pause()
            return await interaction.followup.send("Paused audio.")

    await interaction.followup.send("No audio is currently being played to pause.")
