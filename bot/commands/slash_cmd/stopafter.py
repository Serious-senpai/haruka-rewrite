from discord import app_commands

from _types import Interaction
from core import bot


@bot.slash(
    name="stopafter",
    description="Tell the bot to disconnect after playing the current song",
    official_client=False,
)
@app_commands.guild_only()
async def _stopafter_slash(interaction: Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if not player:
        return await interaction.followup.send("No currently connected player.")

    if await player.switch_stopafter():
        await interaction.followup.send("Enabled `stopafter`. This will be the last song to be played.")
    else:
        await interaction.followup.send("Disabled `stopafter`. Other songs will be played normally after this one ends.")
