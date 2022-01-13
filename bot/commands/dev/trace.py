import tracemalloc
from typing import Literal

from discord.ext import commands

from core import bot


@bot.command(
    name="trace",
    description="Display size of all memory blocks allocated by Python.\nThe indicated `keytype` must be `filename`, `lineno`, or `traceback`, which are the arguments stated in the [documentation](https://docs.python.org/3.9/library/tracemalloc.html#tracemalloc.Snapshot.statistics)",
    usage="trace <keytype>",
)
@commands.is_owner()
async def _trace_cmd(ctx: commands.Context, keytype: Literal["filename", "lineno", "traceback"] = "filename"):
    async with ctx.typing():
        snap = tracemalloc.take_snapshot()

        total_size = sum(trace.size for trace in snap.traces)
        report = "Currently allocating `{:.2f}` MB of memory".format(total_size / 1024 ** 2)

        stats = snap.statistics(keytype, cumulative=True if not keytype == "traceback" else False)
        report += "\nShowing the top 8:```\n" + "\n".join("{:.2f} MB".format(stat.size / 1024 ** 2) + f":: {stat.traceback}" for stat in stats[:8]) + "\n```"

        await ctx.send(report)
