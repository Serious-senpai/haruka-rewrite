import info
from _types import Interaction
from core import bot


@bot.slash(
    name="svinfo",
    description="Get the information about the server",
)
async def _svinfo_slash(interaction: Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be invoked in a server channel.")

    await interaction.response.send_message(embed=info.server_info(interaction.guild))
