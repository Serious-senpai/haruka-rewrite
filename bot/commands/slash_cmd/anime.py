import asyncio

import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import mal, ui


@bot.slash(
    name="anime",
    description="Display anime search results from MyAnimeList",
)
@app_commands.describe(query="The searching query")
async def _anime_slash(interaction: Interaction, query: str):
    await interaction.response.defer()
    if len(query) < 3:
        return await interaction.followup.send("Please provide at least 3 characters in the searching query.")

    results = await mal.MALSearchResult.search(query, criteria="anime", session=interaction.client.session)
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
        anime = await mal.Anime.get(id, session=interaction.client.session)

    if not anime.is_safe() and not getattr(interaction.channel, "nsfw", False):
        return await interaction.followup.send("🔞 This anime contains NSFW content and cannot be displayed in this channel!")

    embed = anime.create_embed()
    embed.set_author(
        name="Anime search result",
        icon_url=interaction.client.user.avatar.url,
    )
    embed.set_footer(text="From myanimelist.net")
    await interaction.followup.send(embed=embed)
