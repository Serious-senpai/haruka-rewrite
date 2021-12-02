from random import randint

from discord.ext import commands

from core import bot


@bot.command(
    name = "roll",
    description = "Generate a random integer between `i` and `j`",
    usage = "roll <i> <j>",
)
@commands.cooldown(1, 4, commands.BucketType.user)
async def _roll_cmd(ctx: commands.Context, i: int, j: int):
    if i < j:
        ans: int = randint(i, j)
    else:
        ans: int = randint(j, i)

    await ctx.send(f"<@!{ctx.author.id}> got **{ans}**")
