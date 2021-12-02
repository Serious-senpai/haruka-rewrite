import traceback
from typing import List

import discord
from discord.ext import commands

from audio import *
from core import bot


@bot.command(
    name = "play",
    description = "Start playing the queue of the voice channel you are connected to.\nThis always plays the music queue as `Repeat All`. If you want something like `Repeat One`, consider making a queue with only 1 song instead.",
)
@commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _play_cmd(ctx: commands.Context):
    if not ctx.author.voice:
        await ctx.send("Please join a voice channel first.")
    else:
        channel: discord.abc.Connectable = ctx.author.voice.channel

        queue: List[str] = await MusicClient.queue(channel.id)
        if len(queue) == 0:
            return await ctx.send("Please add a song to the queue with `add`")

        if ctx.voice_client:
            return await ctx.send("Currently connected to another voice channel in the server. Please use `stop` first.")

        try:
            async with ctx.typing():
                voice_client: MusicClient = await channel.connect(
                    timeout = 30.0,
                    cls = MusicClient,
                )
        except:
            bot.log(f"Error connecting to voice channel {channel.guild}/{channel}")
            bot.log(traceback.format_exc())
            return await ctx.send("Cannot connect to voice channel.")

        await ctx.send(f"Connected to <#{channel.id}>")
        bot.loop.create_task(voice_client.play(target = ctx))
