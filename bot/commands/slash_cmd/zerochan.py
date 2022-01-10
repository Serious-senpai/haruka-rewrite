import random
from typing import Any, Dict, List

import discord

import _zerochan
import slash
from core import bot


json: Dict[str, Any] = {
    "name": "zerochan",
    "type": 1,
    "description": "Search zerochan for an image",
    "options": [{
        "name": "query",
        "description": "The searching query",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _zerochan_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash.parse(interaction)
    query: str = args["query"]
    urls: List[str] = await _zerochan.search(query)
    if not urls:
        return await interaction.followup.send("No matching result was found.")

    embed: discord.Embed = discord.Embed()
    embed.set_image(url=random.choice(urls[:10]))
    embed.set_author(
        name=f"Zerochan search for {query}",
        icon_url=bot.user.avatar.url,
    )
    await interaction.followup.send(embed=embed)
