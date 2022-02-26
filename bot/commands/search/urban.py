import discord
from discord.ext import commands

import _urban
from _types import Context
from core import bot


@bot.command(
    name="urban",
    description="Search for a term from Urban Dictionary",
    usage="urban <query>"
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _urban_cmd(ctx: Context, *, query: str):
    result = await _urban.UrbanSearch.search(query)
    if result:
        embed = result.create_embed()
        embed.set_author(
            name=f"{ctx.author.name} searched for {query}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("No matching result was found.")
