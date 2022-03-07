from typing import Optional

import discord
from discord import app_commands

import saucenao
from _types import Interaction
from core import bot


@bot.slash(
    name="sauce",
    description="Find the image source with saucenao",
)
@app_commands.describe(
    image="The image to get the sauce",
    url="The image URL",
)
async def _sauce_slash(interaction: Interaction, image: Optional[discord.Attachment], url: Optional[str]):
    if image is not None:
        image_url = image.url
    elif url is not None:
        image_url = url
    else:
        return await interaction.response.send_message("Please provide an image URL or an attachment!")

    await interaction.response.defer()
    results = await saucenao.SauceResult.get_sauce(image_url)
    if not results:
        return await interaction.followup.send("Cannot find the image sauce.")

    embed = results[0].create_embed()
    embed.set_author(
        name="Image search result",
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text="For all results, consider using the text command")

    if image is not None and url is not None:
        await interaction.followup.send("Both `image` and `url` were provided, using only the `image` parameter", embed=embed)
    else:
        await interaction.followup.send(embed=embed)
