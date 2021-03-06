from random import randint

from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="roll",
    description="Generate a random integer between `i` and `j`",
    usage="roll <i> <j>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _roll_cmd(ctx: Context, i: int, j: int):
    if i < j:
        ans = randint(i, j)
    else:
        ans = randint(j, i)

    await ctx.send(f"<@!{ctx.author.id}> got **{ans}**")
