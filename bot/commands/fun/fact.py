from discord.ext import commands

import leech
from _types import Context
from core import bot


@bot.command(
    name="fact",
    description="Send you a random fact."
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _fact_cmd(ctx: Context):
    await ctx.send(leech.get_fact())
