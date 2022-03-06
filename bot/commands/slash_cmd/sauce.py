from discord import app_commands

import saucenao
from _types import Interaction
from core import bot


@bot.slash(
    name="sauce",
    description="Find the image source with saucenao",
)
@app_commands.describe(url="The image URL")
async def _sauce_slash(interaction: Interaction, url: str):
    await interaction.response.defer()
    results = await saucenao.SauceResult.get_sauce(url)
    if not results:
        return await interaction.followup.send("Cannot find the image sauce.")

    embed = results[0].create_embed()
    embed.set_author(
        name="Image search result",
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text="For all results, consider using the text command")
    await interaction.followup.send(embed=embed)
