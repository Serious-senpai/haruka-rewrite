import random

import discord

import _tenor
import slash
from core import bot


json = {
    "name": "tenor",
    "type": 1,
    "description": "Search tenor for an image",
    "options": [{
        "name": "query",
        "description": "The searching query",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _tenor_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args = slash.parse(interaction)
    query = args["query"]
    urls = await _tenor.search(query)
    if not urls:
        return await interaction.followup.send("No matching result was found.")

    embed = discord.Embed()
    embed.set_image(url=random.choice(urls[:10]))
    embed.set_author(
        name=f"Tenor search for {query}",
        icon_url=bot.user.avatar.url,
    )
    await interaction.followup.send(embed=embed)
