import slash
import info
from _types import Interaction
from core import bot


json = {
    "name": "svinfo",
    "type": 1,
    "description": "Get the information about the server.",
}


@bot.slash(json)
@slash.guild_only()
async def _svinfo_slash(interaction: Interaction):
    await interaction.response.send_message(embed=info.server_info(interaction.guild))
