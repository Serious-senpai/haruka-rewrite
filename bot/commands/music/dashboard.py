from typing import List

import discord
from discord.ext import commands

import emoji_ui
import _playlist
from core import bot


@bot.command(
    name="dashboard",
    aliases=["db"],
    description="Search for public playlists from the given searching query.",
    usage="dashboard <query>",
)
@commands.cooldown(1, 5, commands.BucketType.user)
async def _dashboard_cmd(ctx: commands.Context, *, query: str):
    results: List[_playlist.Playlist] = await _playlist.Playlist.search(bot, query)
    embeds: List[discord.Embed] = []

    if not results:
        return await ctx.send("No matching result was found.")

    for index, result in enumerate(results):
        embed: discord.Embed = result.create_embed()
        embed.set_author(
            name=f"Displaying result #{index + 1}",
            icon_url=bot.user.avatar.url,
        )
        embeds.append(embed)

    display: emoji_ui.Pagination = emoji_ui.Pagination(embeds)
    await display.send(ctx)
