import contextlib
import textwrap
import traceback

import discord
from discord.ext import commands

import utils
from core import bot


INDENT = " " * 4
bot._eval_task = None


@bot.command(
    name="eval",
    aliases=["exec"],
    description="Evaluate a Python code",
    usage="eval <code>",
)
@commands.is_owner()
@commands.max_concurrency(1)
async def _eval_cmd(ctx: commands.Context, *, code: str):
    code = code.strip("`")
    code = code.removeprefix("python")
    code = code.removeprefix("py")
    code = textwrap.indent(code, INDENT)
    code = code.strip("\n")
    code = f"async def func():\n" + code

    env = {
        "bot": bot,
        "ctx": ctx,
    }
    try:
        exec(code, env, env)
    except BaseException:
        await ctx.send("Cannot create coroutine\n```\n" + traceback.format_exc() + "\n```")
        return

    with open("eval.txt", "w", encoding="utf-8") as writer:
        with contextlib.redirect_stdout(writer):
            with utils.TimingContextManager() as measure:
                bot._eval_task = bot.loop.create_task(env["func"]())

                try:
                    await bot._eval_task
                except BaseException:
                    writer.write(traceback.format_exc())

    await ctx.send(
        f"Process completed after {utils.format(measure.result)}.",
        file=discord.File("eval.txt"),
    )
