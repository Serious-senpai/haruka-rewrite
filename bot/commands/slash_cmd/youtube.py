import asyncio

import discord

import audio
import slash
import ui
import utils
from core import bot


json = {
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


@bot.slash(json)
async def _youtube_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args = slash.parse(interaction)
    query = args["query"]
    if len(query) < 3:
        return await interaction.followup.send(content="Please provide at least 3 characters in the searching query.")

    results = await audio.PartialInvidiousSource.search(query)
    if not results:
        return await interaction.followup.send(content=f"Cannot find any videos from the query `{query}`")

    options = [discord.SelectOption(
        label=result.title[:100],
        description=result.channel[:100],
        value=result.id,
    ) for result in results]

    menu = ui.SelectMenu(placeholder="Select a video", options=options)
    view = ui.DropdownMenu(timeout=120.0)
    view.add_item(menu)
    await view.send(interaction.followup, "Please select a YouTube video from the list below.")

    try:
        id = await menu.result()
    except asyncio.TimeoutError:
        return
    else:
        track = await audio.InvidiousSource.build(id)

    embed = track.create_embed()
    embed.set_author(
        name="YouTube audio request",
        icon_url=bot.user.avatar.url,
    )

    with utils.TimingContextManager() as measure:
        url = await audio.fetch(track)

    if not url:
        embed.set_footer(text="Cannot fetch audio file")
        return await interaction.followup.send(embed=embed)

    embed.add_field(
        name="Audio URL",
        value=f"[Download]({url})",
        inline=False,
    )
    embed.set_footer(text=f"Fetched data in {utils.format(measure.result)}")

    button = discord.ui.Button(style=discord.ButtonStyle.link, url=url, label="Audio URL")
    view = discord.ui.View()
    view.add_item(button)

    await interaction.followup.send(embed=embed, view=view)
