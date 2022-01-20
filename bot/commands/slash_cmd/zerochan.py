import random

import discord

import _zerochan
import slash
from core import bot


json = {
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
    args = slash.parse(interaction)
    query = args["query"]
    urls = await _zerochan.search(query, max_results=20)
    if not urls:
        return await interaction.followup.send("No matching result was found.")

    embed = discord.Embed()
    embed.set_image(url=random.choice(urls))
    embed.set_author(
        name=f"Zerochan search for {query}",
        icon_url=bot.user.avatar.url,
    )
    await interaction.followup.send(embed=embed)
