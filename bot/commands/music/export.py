import io
import json
from typing import List

import discord
from discord.ext import commands

import audio
from core import bot


@bot.command(
    name="export",
    description="Export the voice channel playlist to a file",
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _export_cmd(ctx: commands.Context):
    channel: discord.abc.Connectable = ctx.author.voice.channel
    queue: List[str] = await audio.MusicClient.queue(channel.id)
    if not queue:
        return await ctx.send("This voice channel has no music in its queue!")

    await ctx.send(
        "This is the music queue file. You can import this queue into another voice channel with `import`",
        file=discord.File(io.BytesIO(json.dumps(queue).encode("utf-8")), filename="queue.json"),
    )
