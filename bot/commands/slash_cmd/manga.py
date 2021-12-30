import asyncio
from typing import Any, Dict, List

import discord

import mal
import slash
import ui
from core import bot


json: Dict[str, Any] = {
    "name": "manga",
    "type": 1,
    "description": "Display manga search results from MyAnimeList",
    "options": [{
        "name": "query",
        "description": "The searching query",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _manga_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash.parse(interaction)
    query: str = args["query"]
    if len(query) < 3:
        return await interaction.followup.send("Please provide at least 3 characters in the searching query.")

    results: List[mal.MALSearchResult] = await mal.MALSearchResult.search(query, criteria="manga")
    if not results:
        return await interaction.followup.send("No matching result was found.")

    options: List[discord.SelectOption] = [discord.SelectOption(label=result.title[:100], value=str(result.id)) for result in results]

    menu: ui.SelectMenu = ui.SelectMenu(placeholder="Select a manga", options=options)
    view: ui.DropdownMenu = ui.DropdownMenu(timeout=120.0)
    view.add_item(menu)
    await view.send(interaction.followup, "Please select a manga from the list below.")

    try:
        id: str = await menu.result()
    except asyncio.TimeoutError:
        return
    else:
        manga: mal.Manga = await mal.Manga.get(id)

    em: discord.Embed = manga.create_embed()
    em.set_author(
        name="Manga search result",
        icon_url=bot.user.avatar.url,
    )
    em.set_footer(text="From myanimelist.net")
    await interaction.followup.send(embed=em)
