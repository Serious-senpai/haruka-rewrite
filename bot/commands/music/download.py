import asyncio

import discord
from discord.ext import commands

import audio
import emoji_ui
import utils
from core import bot


@bot.command(
    name="download",
    description="Download the entire music queue of the voice channel you are connected to.",
)
@audio.in_voice()
@commands.cooldown(1, 60, commands.BucketType.user)
async def _download_cmd(ctx: commands.Context):
    channel = ctx.author.voice.channel
    queue = await audio.MusicClient.queue(channel.id)
    if not queue:
        return await ctx.send(f"There aren't any songs in the music queue of channel <#{channel.id}>!")

    if len(queue) > 6:
        return await ctx.send("You cannot use this command for queues with more than 6 songs!")

    async with ctx.typing():
        tracks = []
        tasks = []
        for track_id in queue:
            track = await audio.InvidiousSource.build(track_id)
            tracks.append(track)
            if track is None:
                tasks.append(utils.coro_func(None))
            else:
                tasks.append(audio.fetch(track))

        embeds = []
        results = await asyncio.gather(*tasks)
        for index, result in enumerate(results):
            if result is None:
                track_id = queue[index]
                embed = discord.Embed(description="Cannot fetch this track, most likely the original YouTube video was deleted.")
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
                embeds.append(audio.create_audio_embed(track))

        display = emoji_ui.Pagination(embeds)

    await display.send(ctx.channel)
