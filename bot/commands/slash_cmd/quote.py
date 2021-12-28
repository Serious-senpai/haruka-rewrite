from typing import Any, Dict

import discord

import leech
from core import bot


json: Dict[str, Any] = {
    "name": "quote",
    "type": 1,
    "description": "Send you a random quote.",
}


@bot.slash(json)
async def _quote_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=leech.get_quote())
