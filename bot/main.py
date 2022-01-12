import asyncio
import sys

from discord.ext import commands


if __name__ == "__main__":
    import tracemalloc


    tracemalloc.start()
    with open("./log.txt", "w") as f:
        f.write(f"HARUKA BOT\nRunning on Python {sys.version}\n" + "-" * 50 + "\n")


    from core import bot
    from events import *
    from commands import *
    print(f"Running on {sys.platform}\nPython {sys.version}")

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
            bot._command_count[name] = []

        bot._command_count[name].append(ctx)

    try:
        bot.loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        bot.loop.run_until_complete(asyncio.shield(bot.close()))
    finally:
        bot.cleanup()
