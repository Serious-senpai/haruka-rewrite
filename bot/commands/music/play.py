import asyncio
import traceback

from discord.ext import commands

import audio
from _types import Context
from core import bot


@bot.command(
    name="play",
    description="Start playing the music queue of the voice channel you are connected to.",
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _play_cmd(ctx: Context):
    channel = ctx.author.voice.channel

    queue = await audio.MusicClient.queue(channel.id)
    if len(queue) == 0:
        return await ctx.send("Please add a song to the queue with `add` or `playlist`")

    if ctx.voice_client:
        return await ctx.send("Currently connected to another voice channel in the server. Please use `stop` first.")

    try:
        async with ctx.typing():
            voice_client = await channel.connect(
                timeout=30.0,
                cls=audio.MusicClient,
            )
    except BaseException:
        bot.log(f"Error connecting to voice channel {channel.guild}/{channel}")
        bot.log(traceback.format_exc())
        return await ctx.send("Cannot connect to voice channel.")

    await ctx.send(f"Connected to <#{channel.id}>")
    asyncio.create_task(voice_client.play(target=ctx))
