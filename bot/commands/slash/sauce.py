from typing import Any, Dict

import discord

import slash_utils
from leech import get_sauce
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
    args: Dict[str, str] = slash_utils.parse(interaction)
    results = await get_sauce(args["url"])

    if not results:
        return await interaction.followup.send(content = "Cannot find the image sauce.")

    embed: discord.Embed = results[0]
    embed.title = "Displaying the first result"
    embed.set_footer(text = "For all results, consider using the text command")
    await interaction.followup.send(embed = embed)
