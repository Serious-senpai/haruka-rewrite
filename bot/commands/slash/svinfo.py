from typing import Any, Dict

import discord

import info
from core import bot


json: Dict[str, Any] = {
    "name": "svinfo",
    "type": 1,
    "description": "Get the information about the server.",
}


@bot.slash(json)
async def _svinfo_slash(interaction: discord.Interaction):
    response: discord.InteractionResponse = interaction.response
    if not interaction.guild:
        await response.send_message("This command can only be used in a server.")
    else:
        em: discord.Embed = info.server_info(interaction.guild)
        await response.send_message(embed=em)
