from typing import List

import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import image, utils


@bot.slash(
    name="sfw",
    description="Send a random SFW image",
)
@app_commands.describe(category="The image category")
async def _sfw_slash(interaction: Interaction, category: str):
    await interaction.response.defer()
    await bot.image.wait_until_ready()
    try:
        image_url = await bot.image.get(category, mode="sfw")
    except image.CategoryNotFound:
        return await interaction.followup.send(f"No category named `{category}` was found.")

    if image_url is None:
        return await interaction.followup.send("Cannot fetch any images from this category right now...")

    embed = discord.Embed()
    embed.set_image(url=image_url)
    embed.set_author(
        name="This is your image!",
        icon_url=interaction.client.user.avatar.url,
    )
    await interaction.followup.send(embed=embed)


@_sfw_slash.autocomplete("category")
async def _sfw_autocomplete(interaction: Interaction, current: str) -> List[app_commands.Choice]:
    await interaction.response.defer()
    await bot.image.wait_until_ready()
    results = [app_commands.Choice(name=k, value=k) for k in bot.image.sfw.keys() if current in k]
    if not results:
        best_match = await utils.fuzzy_match(current, bot.image.sfw.keys(), pattern=r"[\w -]+")
        results = [app_commands.Choice(name=best_match, value=best_match)]

    return results[:25]
