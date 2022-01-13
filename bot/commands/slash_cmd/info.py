import discord

import info
import slash
from core import bot


json = {
    "name": "info",
    "type": 1,
    "description": "Get the information about a user.",
    "options": [{
        "name": "user",
        "description": "The target user to retrieve information about.",
        "type": 6,
        "required": False,
    }]
}


@bot.slash(json)
async def info_(interaction: discord.Interaction):
    args = slash.parse(interaction)
    user = args.get("user", interaction.user)

    embed = info.user_info(user)
    await interaction.response.send_message(embed=embed)
