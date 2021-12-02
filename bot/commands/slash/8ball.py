from typing import Any, Dict

import discord

import leech
from core import bot


json: Dict[str, Any] = {
    "name": "8ball",
    "type": 1,
    "description": "Ask the 8ball a question",
    "options": [{
        "name": "question",
        "description": "Concentrate on your question and press `Enter`",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _8ball_slash(interaction: discord.Interaction):
    await interaction.response.send_message(leech.get_8ball())
