from discord.ext import commands

import leech
from core import bot


@bot.command(
    name="8ball",
    aliases=["8b"],
    description="Ask the 8ball a question",
    usage="8ball <question>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _8ball_cmd(ctx: commands.Context, *, question: str):
    await ctx.send(leech.get_8ball())
