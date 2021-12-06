import io
import sys
import time
from typing import Any, Dict, List, Optional

import discord

import audio
import slash_utils
import ui
from core import bot


json: Dict[str, Any] = {
    "name": "youtube",
    "type": 1,
    "description": "Search for a YouTube video and get the mp3 file",
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

        id: str = self.values.pop()
        track: audio.InvidiousSource = await audio.InvidiousSource.build(id)

        em: discord.Embed = track.create_embed()
        em.set_author(
            name="YouTube audio request",
            icon_url=bot.user.avatar.url,
        )

        t: float = time.perf_counter()
        url: Optional[str] = await audio.fetch(track)
        done: float = time.perf_counter() - t

        if not url:
            em.set_footer(text="Cannot fetch audio file")
            return await interaction.followup.send(embed=em)

        em.add_field(
            name="Audio URL",
            value=f"[Download]({url})",
            inline=False,
        )
        em.set_footer(text="Fetched data in {:.2f} ms".format(1000 * done))

        await interaction.followup.send(embed=em)


@bot.slash(json)
async def _youtube_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash_utils.parse(interaction)
    query: str = args["query"]
    if len(query) < 3:
        return await interaction.followup.send(content="Please provide at least 3 characters in the searching query.")

    results: List[audio.PartialInvidiousSource] = await audio.PartialInvidiousSource.search(query)
    if not results:
        return await interaction.followup.send(content=f"Cannot find any videos from the query `{query}`")

    options: List[discord.SelectOption] = [discord.SelectOption(
        label=result.title[:100],
        description=result.channel[:100],
        value=result.id,
    ) for result in results]

    menu: Menu = Menu(
        placeholder="Select a video",
        options=options,
    )
    view: ui.View = ui.View(timeout=120.0)
    view.add_item(menu)
    await view.send(interaction.followup, "Please select a YouTube video from the list below.")
