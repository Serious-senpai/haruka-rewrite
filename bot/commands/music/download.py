import asyncio

import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import audio, emoji_ui, emojis, utils


@bot.command(
    name="download",
    description="Download the entire music queue of the voice channel you are connected to.",
)
@bot.audio.in_voice()
@commands.cooldown(1, 60, commands.BucketType.user)
async def _download_cmd(ctx: Context):
    channel = ctx.author.voice.channel
    queue = await bot.audio.queue(channel.id)
    if not queue:
        return await ctx.send(f"There aren't any songs in the music queue of channel <#{channel.id}>!")

    if len(queue) > 6:
        return await ctx.send("You cannot use this command for queues with more than 6 songs!")

    async with ctx.typing():
        tracks = []
        tasks = []
        for track_id in queue:
            track = await bot.audio.build(audio.InvidiousSource, track_id)
            tracks.append(track)
            if track is None:
                tasks.append(utils.coro_func(None))
            else:
                tasks.append(bot.audio.fetch(track))

        embeds = []
        results = await asyncio.gather(*tasks)
        for index, result in enumerate(results):
            if result is None:
                track_id = queue[index]
                embed = discord.Embed(description=f"{emojis.MIKUCRY} Cannot fetch this track, most likely the original YouTube video was deleted.")
                embed.set_author(
                    name="Warning",
                    icon_url=bot.user.avatar.url,
                )
                embed.add_field(
                    name="YouTube URL",
                    value=f"https://www.youtube.com/watch?v={track_id}",
                )
                embeds.append(embed)
            else:
                track = tracks[index]
                embeds.append(bot.audio.create_audio_embed(track))

        display = emoji_ui.Pagination(bot, embeds)

    await display.send(ctx.channel)
