import slash
import _urban
from _types import Interaction
from core import bot


json = {
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
async def _urban_slash(interaction: Interaction):
    await interaction.response.defer()
    args = slash.parse(interaction)
    query = args["word"]

    result = await _urban.UrbanSearch.search(query)
    if result:
        embed = result.create_embed()
        embed.set_author(
            name=f"This is the definition of {query}",
            icon_url=bot.user.avatar.url,
        )
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(content="No matching result was found.")
