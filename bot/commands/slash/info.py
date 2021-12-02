from typing import Any, Dict

import discord

import info
import slash_utils
from core import bot


json: Dict[str, Any] = {
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
    args: Dict[str, discord.User] = slash_utils.parse(interaction)
    user: discord.User = args.get("user", interaction.user)

    em: discord.Embed = info.user_info(user)
    await interaction.response.send_message(embed = em)
