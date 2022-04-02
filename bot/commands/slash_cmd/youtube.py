import asyncio

import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import audio, emojis, ui, utils


@bot.slash(
    name="youtube",
    description="Search for a YouTube video and get the mp3 file",
)
@app_commands.describe(query="The searching query")
async def _youtube_slash(interaction: Interaction, query: str):
    await interaction.response.defer()
    if len(query) < 3:
        return await interaction.followup.send(content="Please provide at least 3 characters in the searching query.")

    results = await bot.audio.search(query)
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
        track_id = await menu.result()
    except asyncio.TimeoutError:
        return
    else:
        track = await bot.audio.build(audio.InvidiousSource, track_id)

    if track is None:
        return await interaction.followup.send(f"{emojis.MIKUCRY} Cannot fetch track ID `{track_id}`")

    with utils.TimingContextManager() as measure:
        url = await bot.audio.fetch(track)

    if url is None:
        embed = track.create_embed()
        embed.set_footer(text="Cannot fetch this track")
        await interaction.followup.send(embed=embed)

    else:
        embed = bot.audio.create_audio_embed(track)
        embed.set_footer(text=f"Fetched data in {utils.format(measure.result)}")
        button = discord.ui.Button(style=discord.ButtonStyle.link, url=url, label="Audio URL")
        view = discord.ui.View()
        view.add_item(button)

        await interaction.followup.send(embed=embed, view=view)
