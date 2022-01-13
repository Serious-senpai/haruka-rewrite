import asyncio
import io
import textwrap
import traceback
from typing import Any

import discord
from discord.ext import commands

import utils
from core import bot


INDENT = " " * 4
IN_PROGRESS = asyncio.Event()
IN_PROGRESS.set()
bot._eval_task = None


def write(content: Any):
    with open("eval.txt", "w", encoding="utf-8") as f:
        f.write(content)


@bot.command(
    name="eval",
    aliases=["exec"],
    description="Evaluate a Python code",
    usage="eval <code>",
)
@commands.is_owner()
async def _eval_cmd(ctx: commands.Context, *, code: str):
    if not IN_PROGRESS.is_set():
        return await ctx.send("Another `eval` operation is in progress, please wait for it to terminate.")

    output = io.StringIO()
    env = {}
    env.update(__stdout=output, bot=bot, ctx=ctx)

    code = code.strip("`")
    code = code.removeprefix("python")
    code = code.removeprefix("py")
    code = textwrap.indent(code, INDENT * 2)
    code = code.strip("\n")
    code = f"import contextlib\nasync def __exec():\n{INDENT}with contextlib.redirect_stdout(__stdout):\n" + code

    IN_PROGRESS.clear()

    try:
        exec(code, env)
    except BaseException:
        await ctx.send("Cannot create coroutine:\n```\n" + traceback.format_exc() + "\n```")
        return IN_PROGRESS.set()

    with utils.TimingContextManager() as measure:
        bot._eval_task = bot.loop.create_task(locals()["env"]["__exec"]())

        try:
            await bot._eval_task
        except asyncio.CancelledError:
            pass
        except BaseException:
            output.write(traceback.format_exc())

    IN_PROGRESS.set()
    content = output.getvalue()

    if content:
        await asyncio.to_thread(write, content)

        await ctx.send(
            f"Process completed after {utils.format(measure.result)}.",
            file=discord.File("eval.txt"),
        )
    else:
        await ctx.send(f"Process completed after {utils.format(measure.result)}.")
