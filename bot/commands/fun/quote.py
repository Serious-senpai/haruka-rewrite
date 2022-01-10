from discord.ext import commands

import leech
from core import bot


@bot.command(
    name="quote",
    description="Send you a random anime quote.",
    usage="quote <anime | default: random>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _quote_cmd(ctx: commands.Context, *, anime: str = None):
    await ctx.send(embed=await leech.get_quote(anime))
