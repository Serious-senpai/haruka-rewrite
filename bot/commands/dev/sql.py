from discord.ext import commands

import utils
from core import bot


@bot.command(
    name="sql",
    description="Perform a SQL query",
    usage="sql <query>",
)
@commands.is_owner()
async def _sql_cmd(ctx: commands.Context, *, query):
    try:
        with utils.TimingContextManager() as measure:
            status: str = await bot.conn.execute(query)
    except Exception as ex:
        await ctx.send(f"An exception occured: {ex}")
    else:
        await ctx.send(f"Process executed in {utils.format(measure.result)}\n```\n{status}\n```")
