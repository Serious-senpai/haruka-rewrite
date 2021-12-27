from discord.ext import commands

import leech
from core import bot


@bot.command(
    name="quote",
    description="Send you a random anime quote."
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _quote_cmd(ctx: commands.Context):
    await ctx.send(embed=leech.get_quote())
