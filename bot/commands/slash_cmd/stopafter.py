from _types import Interaction
from core import bot


@bot.slash(
    name="stopafter",
    description="Tell the bot to disconnect after playing the current song",
)
async def _stopafter_slash(interaction: Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be invoked in a server channel.")

    await interaction.response.defer()
    player = interaction.guild.voice_client

    if not player:
        return await interaction.followup.send("No currently connected player.")

    player._stopafter = not player._stopafter
    if player._stopafter:
        await interaction.followup.send("Enabled `stopafter`. This will be the last song to be played.")
    else:
        await interaction.followup.send("Disabled `stopafter`. Other songs will be played normally after this one ends.")
