import asyncio
import time

import discord
from discord.ext import commands

from core import bot


def save_to(content: str) -> discord.File:
    with open("./ssh.txt", "w") as f:
        f.write(content)
    return discord.File("./ssh.txt")


@bot.command(
    name = "ssh",
    aliases = ["bash", "sh"],
    description = "Execute a bash command",
    usage = "ssh <command>",
)
@commands.is_owner()
async def _ssh_cmd(ctx: commands.Context, *, cmd: str):
    process: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
        cmd,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.STDOUT,
    )

    try:
        t: float = time.perf_counter()
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout = 30.0)
        _t: float = time.perf_counter()
    except asyncio.TimeoutError:
        process.kill()
        await ctx.send(f"Process didn't complete within 30 seconds and was killed. Return code `{process.returncode}`")
    else:
        output: str = stdout.decode("utf-8")
        notify: str = f"Process completed with return code {process.returncode}" + " after {:.2f} ms".format(1000 * (_t - t))

        if output:
            f: discord.File = await asyncio.to_thread(save_to, output)
            await ctx.send(notify, file = f)
        else:
            await ctx.send(notify)
