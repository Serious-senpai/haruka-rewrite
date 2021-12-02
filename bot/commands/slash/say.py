from typing import Any, Dict

import discord

import slash_utils
from core import bot


json: Dict[str, Any] = {
    "name": "say",
    "type": 1,
    "description": "Say something, can be used to send animated emojis.",
    "options": [{
        "name": "content",
        "description": "The string to repeat",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _say_slash(interaction: discord.Interaction):
    args: Dict[str, str] = slash_utils.parse(interaction)
    await interaction.response.send_message(args["content"])
