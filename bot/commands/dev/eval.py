import asyncio
import io
import textwrap
import time
import traceback
from typing import Any, Dict

import discord
from discord.ext import commands

from core import bot


INDENT: str = " " * 4
IN_PROGRESS: asyncio.Event = asyncio.Event()
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

    output: io.StringIO = io.StringIO()
    env: Dict[str, Any] = {
        "bot": bot,
        "ctx": ctx,
        "__stdout": output,
    }

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

    t: float = time.perf_counter()
    bot._eval_task = bot.loop.create_task(locals()["env"]["__exec"]())

    try:
        await bot._eval_task
    except asyncio.CancelledError:
        pass
    except BaseException:
        output.write(traceback.format_exc())

    _t: float = time.perf_counter()
    IN_PROGRESS.set()
    content: str = output.getvalue()

    if content:
        await asyncio.to_thread(write, content)

        await ctx.send(
            "Process completed after {:.2f} ms.".format(1000 * (_t - t)),
            file=discord.File("eval.txt"),
        )
    else:
        await ctx.send("Process completed after {:.2f} ms.".format(1000 * (_t - t)))
