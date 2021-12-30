from typing import Any, Dict, List

import discord

import mal
import slash
import ui
from core import bot


json: Dict[str, Any] = {
    "name": "anime",
    "type": 1,
    "description": "Display anime search results from MyAnimeList",
    "options": [{
        "name": "query",
        "description": "The searching query",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _anime_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash.parse(interaction)
    query: str = args["query"]
    if len(query) < 3:
        return await interaction.followup.send("Please provide at least 3 characters in the searching query.")

    results: List[mal.MALSearchResult] = await mal.MALSearchResult.search(query, criteria="anime")
    if not results:
        await interaction.followup.send("No matching result was found.")

    options: List[discord.SelectOption] = [discord.SelectOption(label=result.title[:100], value=str(result.id)) for result in results]

    menu: ui.SelectMenu = ui.SelectMenu(placeholder="Select an anime", options=options)
    view: ui.DropdownView = ui.DropdownView(timeout=120.0)
    view.add_item(menu)
    await view.send(interaction.followup, "Please select an anime from the list below.")

    id: str = await menu.result()
    anime: mal.Anime = await mal.Anime.get(id)

    em: discord.Embed = anime.create_embed()
    em.set_author(
        name="Anime search result",
        icon_url=bot.user.avatar.url,
    )
    em.set_footer(text="From myanimelist.net")
    await interaction.followup.send(embed=em)
