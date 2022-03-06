import asyncio

import discord
from discord import app_commands

import mal
import ui
from _types import Interaction
from core import bot


@bot.slash(
    name="anime",
    description="Display anime search results from MyAnimeList",
)
@app_commands.describe(query="The searching query")
async def _anime_slash(interaction: Interaction, query: str):
    await interaction.response.defer()
    if len(query) < 3:
        return await interaction.followup.send("Please provide at least 3 characters in the searching query.")

    results = await mal.MALSearchResult.search(query, criteria="anime")
    if not results:
        return await interaction.followup.send("No matching result was found.")

    options = [discord.SelectOption(label=result.title[:100], value=str(result.id)) for result in results]

    menu = ui.SelectMenu(placeholder="Select an anime", options=options)
    view = ui.DropdownMenu(timeout=120.0)
    view.add_item(menu)
    await view.send(interaction.followup, "Please select an anime from the list below.")

    try:
        id = await menu.result()
    except asyncio.TimeoutError:
        return
    else:
        anime = await mal.Anime.get(id)

    embed = anime.create_embed()
    embed.set_author(
        name="Anime search result",
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text="From myanimelist.net")
    await interaction.followup.send(embed=embed)
