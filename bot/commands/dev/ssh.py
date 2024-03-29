import asyncio
from os import path

import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import utils


@bot.command(
    name="ssh",
    aliases=["bash", "sh"],
    description="Execute a bash command",
    usage="ssh <command>",
)
@commands.is_owner()
@commands.max_concurrency(1)
async def _ssh_cmd(ctx: Context, *, cmd: str):
    with open("./bot/web/assets/ssh.txt", "w", encoding="utf-8") as writer:
        with utils.TimingContextManager() as measure:
            try:
                process = await asyncio.create_subprocess_shell(cmd, stdout=writer, stderr=writer)
                await process.communicate()
            except asyncio.TimeoutError:
                process.kill()

    await ctx.send(
        f"Process completed with return code {process.returncode} after {utils.format(measure.result)}",
        file=discord.File("./bot/web/assets/ssh.txt") if path.getsize("./bot/web/assets/ssh.txt") > 0 else None,
    )
