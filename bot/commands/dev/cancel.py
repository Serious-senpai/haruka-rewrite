from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="cancel",
    description="Cancel the running `eval` task",
)
@commands.is_owner()
async def _cancel_cmd(ctx: Context):
    if bot._eval_task:
        bot._eval_task.cancel()
        bot._eval_task = None
        await ctx.send("Cancelled.")

    else:
        await ctx.send("No running `eval` task.")
