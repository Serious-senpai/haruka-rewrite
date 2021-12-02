from typing import Any, Dict, List

import discord

import mal
import slash_utils
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


class Menu(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()

        value: str = self.values.pop()
        manga: mal.Manga = await mal.Manga.get(value)

        em: discord.Embed = manga.create_embed()
        em.set_author(
            name = "Manga search result",
            icon_url = bot.user.avatar.url,
        )
        em.set_footer(text = "From myanimelist.net")
        await interaction.followup.send(embed = em)


@bot.slash(json)
async def _manga_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash_utils.parse(interaction)
    query: str = args["query"]
    if len(query) < 3:
        return await interaction.followup.send("Please provide at least 3 characters in the searching query.")

    results = await mal.MALSearchResult.search(
        query,
        criteria = "manga",
    )
    if not results:
        await interaction.followup.send(content = "No matching result was found.")

    options: List[discord.SelectOption] = [discord.SelectOption(label = result.title[:100], value = str(result.id)) for result in results]

    menu: Menu = Menu(
        placeholder = "Select a manga",
        options = options,
    )
    view: ui.View = ui.View(timeout = 120.0)
    view.add_item(menu)
    await view.send(interaction.followup, "Please select a manga from the list below.")
