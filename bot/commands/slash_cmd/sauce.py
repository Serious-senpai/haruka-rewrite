import saucenao
import slash
from _types import Interaction
from core import bot


json = {
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
async def _sauce_slash(interaction: Interaction):
    await interaction.response.defer()
    args = slash.parse(interaction)
    results = await saucenao.SauceResult.get_sauce(args["url"])
    if not results:
        return await interaction.followup.send("Cannot find the image sauce.")

    embed = results[0].create_embed()
    embed.set_author(
        name="Image search result",
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text="For all results, consider using the text command")
    await interaction.followup.send(embed=embed)
