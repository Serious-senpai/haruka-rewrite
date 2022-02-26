import asyncio

import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="tasks",
    aliases=["task"],
    description="View running `asyncio.Task`s",
)
@commands.is_owner()
async def tasks_cmd(ctx: Context):
    with open("./tasks.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(task.__repr__() for task in asyncio.all_tasks()))
    await ctx.send(file=discord.File("./tasks.txt"))
