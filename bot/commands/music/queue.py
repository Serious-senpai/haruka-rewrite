import discord
from discord.ext import commands

import audio
import emoji_ui
from core import bot


SONGS_PER_PAGE = 8


@bot.command(
    name="queue",
    description="View the music queue of a voice channel"
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _queue_cmd(ctx: commands.Context):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel = ctx.author.voice.channel
    track_ids = await audio.MusicClient.queue(channel.id)
    pages = 1 + len(track_ids) // SONGS_PER_PAGE

    counter = 0
    embeds = []

    async with ctx.typing():
        for page in range(pages):
            embed = discord.Embed(title=f"Music queue of channel {channel.name}")
            embed.set_footer(text=f"Currently has {len(track_ids)} song(s) | Page {page + 1}/{pages}")

            for _ in range(SONGS_PER_PAGE):
                try:
                    track = await audio.PartialInvidiousSource.build(track_ids[counter])
                except IndexError:
                    break

                counter += 1
                embed.add_field(
                    name=f"**#{counter}** {track.title}",
                    value=track.channel,
                    inline=False,
                )

            embeds.append(embed)

    display = emoji_ui.NavigatorPagination(embeds)
    await display.send(ctx)
