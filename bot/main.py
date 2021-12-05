﻿import asyncio
import contextlib
import multiprocessing
import os
import sys

from discord.ext import commands


def _run_server():
    with contextlib.suppress(KeyboardInterrupt):
        if sys.platform == "win32":
            os.system("py ./bot/server/server.py")
        else:
            os.system("python3 ./bot/server/server.py")


if __name__ == "__main__":
    import tracemalloc
    tracemalloc.start()

    with open("./log.txt", "w") as f:
        line: str = "-" * 50
        f.write(f"{line}\nHARUKA BOT\nRunning on Python {sys.version}\n{line}\n")

    print(f"Running on {sys.platform}\nPython {sys.version}")
    process: multiprocessing.Process = multiprocessing.Process(target=_run_server)
    print("Server is starting")
    process.start()

    from core import bot
    from events import *
    from commands import *

    @bot.event
    async def on_ready():
        bot.log(f"Logged in as {bot.user}")
        print(f"Logged in as {bot.user}")

    @bot.before_invoke
    async def _before_invoke(ctx: commands.Context):
        # Count text commands
        if ctx.command.root_parent:
            return

        if await bot.is_owner(ctx.author):
            return

        name: str = ctx.command.name
        if name not in bot._command_count:
            bot._command_count[name] = 0

        bot._command_count[name] += 1

    try:
        bot.loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        bot.loop.run_until_complete(asyncio.shield(bot.close()))
    finally:
        bot.cleanup()
        process.join()
