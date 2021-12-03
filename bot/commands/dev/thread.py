import threading

import discord
from discord.ext import commands

from core import bot


@bot.command(
    name="thread",
    aliases=["threads"],
    description="Display list of active threads.",
)
@commands.is_owner()
async def _thread_cmd(ctx: commands.Context):
    content: str = "\n".join(f"Thread '{thread.name}':\n\tThread ID (TID): {thread.native_id}\n\tAlive: {thread.is_alive()}\n\tDaemon: {thread.isDaemon()}" for thread in threading.enumerate())
    string: str = f"Currently running {len(threading.enumerate())} threads:\n```\n{content}\n```"

    if len(string) > 2000:
        with open("./thread.txt", "w") as f:
            f.write(content)
        await ctx.send(f"Currently running {len(threading.enumerate())} threads", file=discord.File("./thread.txt"))

    else:
        await ctx.send(string)
