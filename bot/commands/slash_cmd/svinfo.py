from discord import app_commands

from _types import Interaction
from core import bot
from lib import info


@bot.slash(
    name="svinfo",
    description="Get the information about the server",
)
@app_commands.guild_only()
async def _svinfo_slash(interaction: Interaction):
    await interaction.response.send_message(embed=info.server_info(interaction.guild))
