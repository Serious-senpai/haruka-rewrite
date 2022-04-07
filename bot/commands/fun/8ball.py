from discord.ext import commands

from _types import Context
from core import bot
from lib import resources


@bot.command(
    name="8ball",
    aliases=["8b"],
    description="Ask the 8ball a question",
    usage="8ball <question>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _8ball_cmd(ctx: Context, *, question: str):
    await ctx.send(resources.get_8ball())
