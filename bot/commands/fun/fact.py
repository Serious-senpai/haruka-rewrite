from discord.ext import commands

from _types import Context
from core import bot
from lib import resources


@bot.command(
    name="fact",
    description="Send you a random fact."
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _fact_cmd(ctx: Context):
    await ctx.send(resources.get_fact())
