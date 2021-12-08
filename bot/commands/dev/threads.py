import threading

import discord
from discord.ext import commands

from core import bot


@bot.command(
    name="threads",
    aliases=["thread"],
    description="View running threads",
)
@commands.is_owner()
async def _threads_cmd(ctx: commands.Context):
    with open("./threads.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"Thread name='{thread.name}' ident={thread.ident} TID={thread.native_id} daemon={thread.daemon} alive={thread.is_alive()}" for thread in threading.enumerate()))
    await ctx.send(file=discord.File("./threads.txt"))
