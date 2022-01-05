from typing import Optional

import discord
from discord.ext import commands

import _urban
from core import bot


@bot.command(
    name="urban",
    description="Search for a term from Urban Dictionary",
    usage="urban <query>"
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _urban_cmd(ctx: commands.Context, *, query: str):
    result: Optional[_urban.UrbanSearch] = await _urban.UrbanSearch.search(query)
    if result:
        em: discord.Embed = result.create_embed()
        em.set_author(
            name=f"{ctx.author.name} searched for {query}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
        await ctx.send(embed=em)
    else:
        await ctx.send("No matching result was found.")
