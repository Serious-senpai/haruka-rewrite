import asyncio
from types import FrameType
from typing import List

import discord
from discord.ext import commands

from core import bot


def _display_frame(task: asyncio.Task) -> str:
    frames: List[FrameType] = task.get_stack()
    if not frames:
        return "None"

    frame: FrameType = frames.pop()  # oldest
    return f"{frame.f_code.co_filename}::{frame.f_code.co_firstlineno}"


@bot.command(
    name="tasks",
    aliases=["task"],
    description=f"View running `asyncio.Task`s",
)
@commands.is_owner()
async def tasks_cmd(ctx: commands.Context):
    with open("./tasks.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"Task name='{task.get_name()}' coro={task.get_coro().__name__} done={task.done()} frame={_display_frame(task)}" for task in asyncio.all_tasks()))
    await ctx.send(file=discord.File("./tasks.txt"))
