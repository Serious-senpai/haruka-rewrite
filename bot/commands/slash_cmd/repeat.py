from _types import Interaction
from core import bot


json = {
    "name": "repeat",
    "type": 1,
    "description": "Switch between REPEAT_ONE and REPEAT_ALL",
}


@bot.slash(
    name="repeat",
    description="Switch between REPEAT_ONE and REPEAT_ALL",
)
async def _repeat_slash(interaction: Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be invoked in a server channel.")

    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player:
        await player.operable.wait()
        player._repeat = not player._repeat

        if player._repeat:
            await interaction.followup.send("Switched to `REPEAT ONE` mode. The current song will be played repeatedly.")
        else:
            await interaction.followup.send("Switched to `REPEAT ALL` mode. All songs will be played as normal.")

    else:
        await interaction.followup.send("No audio is currently being played.")
