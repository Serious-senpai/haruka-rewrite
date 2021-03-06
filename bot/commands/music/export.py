import io
import json

import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="export",
    description="Export the voice channel playlist to a file",
)
@bot.audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _export_cmd(ctx: Context):
    channel = ctx.author.voice.channel
    queue = await bot.audio.queue(channel.id)
    if not queue:
        return await ctx.send("This voice channel has no music in its queue!")

    await ctx.send(
        f"This is the music queue file.\nYou can import this queue into another voice channel with `{ctx.clean_prefix}import`",
        file=discord.File(io.BytesIO(json.dumps(queue).encode("utf-8")), filename="queue.json"),
    )
