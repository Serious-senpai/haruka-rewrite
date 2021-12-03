import time

from discord.ext import commands

from core import bot


@bot.command(
    name="sql",
    description="Perform a SQL query",
    usage="sql <query>",
)
@commands.is_owner()
async def _sql_cmd(ctx: commands.Context, *, query):
    try:
        start: float = time.perf_counter()
        status: str = await bot.conn.execute(query)
        end: float = time.perf_counter()
    except Exception as ex:
        await ctx.send(f"An exception occured: {ex}")
    else:
        await ctx.send(f"Process executed in {1000 * (end - start)} ms\n```\n{status}\n```")
