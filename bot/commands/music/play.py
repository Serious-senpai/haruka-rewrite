import traceback

from discord.ext import commands

from _types import Context
from core import bot
from lib import audio


@bot.command(
    name="play",
    description="Start playing the music queue of the voice channel you are connected to.",
)
@bot.audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _play_cmd(ctx: Context):
    channel = ctx.author.voice.channel
    prefix = ctx.clean_prefix

    queue = await bot.audio.queue(channel.id)
    if len(queue) == 0:
        return await ctx.send(f"Please add a song to the queue with `{prefix}add` or `{prefix}playlist`")

    if ctx.voice_client:
        return await ctx.send(f"Currently connected to another voice channel in the server. Please use `{prefix}stop` first.")

    try:
        async with ctx.typing():
            voice_client = await channel.connect(timeout=30.0, cls=audio.MusicClient)
    except BaseException:
        bot.log(f"Error connecting to voice channel {channel.guild}/{channel}")
        bot.log(traceback.format_exc())
        return await ctx.send("Cannot connect to voice channel.")

    await ctx.send(f"Connected to <#{channel.id}>")
    bot.loop.create_task(voice_client.play(target=ctx))
