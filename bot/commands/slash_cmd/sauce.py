from typing import Any, Dict, List

import discord

import saucenao
import slash
from core import bot


json: Dict[str, Any] = {
    "name": "sauce",
    "type": 1,
    "description": "Find the image source with saucenao",
    "options": [{
        "name": "url",
        "description": "The URL to the image",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _sauce_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash.parse(interaction)
    results: List[saucenao.SauceResult] = await saucenao.SauceResult.get_sauce(args["url"])
    if not results:
        return await interaction.followup.send("Cannot find the image sauce.")

    embed: discord.Embed = results[0].create_embed()
    embed.set_author(
        name="Image search result",
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text="For all results, consider using the text command")
    await interaction.followup.send(embed=embed)
