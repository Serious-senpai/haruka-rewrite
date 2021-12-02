import asyncio
import time
from typing import List

import discord
from discord.ext import commands

from core import bot


BOMP_PING_CACHE: List[int] = []


@bot.command(
    name = "ping",
    description = "Ping someone and measure their response speed.\nTry breaking the record of 0.01 sec.",
    usage = "ping <user>",
)
@commands.cooldown(1, 4, commands.BucketType.user)
async def _ping_cmd(ctx: commands.Context, user: discord.User = None):
    if not user:
        await ctx.send(f"Who do you want to ping, <@!{ctx.author.id}>?")

    elif user.id == ctx.author.id and user.id in BOMP_PING_CACHE:
        await ctx.send(f"<@!{ctx.author.id}> Eat this bomb 💣💥💥")

    elif user.id == ctx.author.id:
        BOMP_PING_CACHE.append(ctx.author.id)
        await ctx.send(f"<@!{ctx.author.id}> Try pinging yourself again and I will ping you with a bomb instead 💣")

    elif user.id == bot.user.id:
        await ctx.send("DON'T PING ME! 💣💥💥")

    else:
        await ctx.message.add_reaction("🏓")
        start: float = time.perf_counter()

        def check(message):
            return message.author.id == user.id and message.channel.id == ctx.channel.id

        try:
            _ = await bot.wait_for("message", check = check, timeout = 300.0)
        except asyncio.TimeoutError:
            await ctx.message.reply(f"<@!{user.id}> hasn't sent any messages in 5 minutes, ping request timed out.")
        else:
            end: float = time.perf_counter()
            await ctx.message.reply(f"🏓 Pong! <@!{user.id}> responded in " + "{:.2f} seconds".format(end - start))
