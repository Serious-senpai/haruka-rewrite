from typing import Optional

import discord
from discord.ext import commands

import _playlist
from core import bot


@bot.command(
    name="unpublish",
    description="Unpublish a public playlist you published.",
    usage="unpublish <playlist ID>",
)
@commands.cooldown(1, 5, commands.BucketType.user)
async def _unpublish_cmd(ctx: commands.Context, id: int):
    result: Optional[_playlist.Playlist] = await _playlist.Playlist.get(bot, id)
    if not result:
        return await ctx.send(f"No playlist with ID `{id}`")

    if not result.author == ctx.author:
        return await ctx.send("You do not own this playlist!")

    await bot.conn.execute("DELETE FROM playlist WHERE id = $1", id)

    embed: discord.Embed = result.create_embed()
    embed.set_author(
        name="Unpublished 1 playlist",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    await ctx.send(embed=embed)
