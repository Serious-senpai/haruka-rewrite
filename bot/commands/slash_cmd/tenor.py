import random

import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import tenor


@bot.slash(
    name="tenor",
    description="Search tenor for an image",
)
@app_commands.describe(query="The searching query")
async def _tenor_slash(interaction: Interaction, query: str):
    await interaction.response.defer()
    urls = await tenor.search(query, session=interaction.client.session)
    if not urls:
        return await interaction.followup.send("No matching result was found.")

    embed = discord.Embed()
    embed.set_image(url=random.choice(urls[:10]))
    embed.set_author(
        name=f"Tenor search for {query}",
        icon_url=interaction.client.user.avatar.url,
    )
    await interaction.followup.send(embed=embed)
