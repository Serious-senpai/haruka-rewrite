from typing import Optional

import discord
from discord.ext import commands

import leech
from core import bot


@bot.command(
    name="quote",
    description="Send you a random anime quote."
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _quote_cmd(ctx: commands.Context):
    embed: Optional[discord.Embed]
    try:
        embed = await leech.get_quote()
    except BaseException:
        embed = None

    if embed:
        await ctx.send(embed=embed)
    else:
        await ctx.send("Cannot find any quotes right now!")
