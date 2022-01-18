import discord

import _pixiv
import slash
from core import bot


json = {
    "name": "pixiv",
    "type": 1,
    "description": "Search for an artwork from Pixiv",
    "options": [{
        "name": "string",
        "description": "The searching query, a URL or an ID",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _pixiv_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args = slash.parse(interaction)
    query = args["string"]

    parsed = await _pixiv.parse(query, session=bot.session)
    if isinstance(parsed, list):
        try:
            parsed = parsed[0]
        except IndexError:
            return await interaction.followup.send("No matching result was found.")

    await interaction.followup.send(embed=await parsed.create_embed(session=bot.session))
