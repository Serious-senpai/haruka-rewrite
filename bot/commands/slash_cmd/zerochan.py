import random

import discord
from discord import app_commands

import _zerochan
from _types import Interaction
from core import bot


@bot.slash(
    name="zerochan",
    description="Search zerochan for an image",
)
@app_commands.describe(query="The searching query")
async def _zerochan_slash(interaction: Interaction, query: str):
    await interaction.response.defer()
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
