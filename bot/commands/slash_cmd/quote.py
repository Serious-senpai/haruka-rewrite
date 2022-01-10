from typing import Any, Dict, Optional

import discord

import leech
import slash
from core import bot


json: Dict[str, Any] = {
    "name": "quote",
    "type": 1,
    "description": "Send you a random anime quote.",
    "options": [{
        "name": "anime",
        "description": "The anime name to get the quote, leave blank to get a random one.",
        "type": 3,
        "required": False,
    }]
}


@bot.slash(json)
async def _quote_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash.parse(interaction)
    anime: Optional[str] = args.get("anime")
    await interaction.followup.send(embed=await leech.get_quote(anime))
