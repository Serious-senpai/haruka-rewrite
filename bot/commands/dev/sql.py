import traceback

from discord.ext import commands

from _types import Context
from core import bot
from lib import utils


@bot.command(
    name="sql",
    description="Perform a SQL query",
    usage="sql <query>",
)
@commands.is_owner()
async def _sql_cmd(ctx: Context, *, query):
    try:
        with utils.TimingContextManager() as measure:
            status = await bot.conn.execute(query)
    except BaseException:
        await ctx.send("```\n" + traceback.format_exc() + "\n```")
    else:
        await ctx.send(f"Process executed in {utils.format(measure.result)}\n```\n{status}\n```")
