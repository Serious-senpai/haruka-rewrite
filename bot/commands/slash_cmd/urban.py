from typing import Any, Dict, Optional

import discord

import slash
import urban
from core import bot


json: Dict[str, Any] = {
    "name": "urban",
    "type": 1,
    "description": "Search Urban Dictionary for a term",
    "options": [{
        "name": "word",
        "description": "The word to look up",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _urban_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash.parse(interaction)
    query: str = args["word"]

    result: Optional[urban.UrbanSearch] = await urban.UrbanSearch.search(query)
    if result:
        em: discord.Embed = result.create_embed()
        em.set_author(
            name=f"This is the definition of {query}",
            icon_url=bot.user.avatar.url,
        )
        await interaction.followup.send(embed=em)
    else:
        await interaction.followup.send(content="No matching result was found.")
