import contextlib

import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="rickroll",
    aliases=["rr", "nggyu"],
    description="Send a rickroll video",
)
@commands.cooldown(1, 3, commands.BucketType.user)
async def _rickroll_cmd(ctx: Context):
    with contextlib.suppress(discord.Forbidden):
        await ctx.message.delete()
    await ctx.send(file=discord.File("./bot/assets/misc/video0.mp4"))
