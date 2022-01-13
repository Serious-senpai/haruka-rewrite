import discord
from discord.ext import commands

import audio
import emoji_ui
from core import bot


SONGS_PER_PAGE = 8
INLINE = False


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

    names = []
    values = []
    index = []

    async with ctx.typing():
        for _index, track_id in enumerate(track_ids):
            track = await audio.PartialInvidiousSource.build(track_id)
            if track:
                names.append(f"**#{_index + 1}** {track.title}")
                values.append(track.channel)
            else:
                names.append(f"**#{_index + 1}** *Unknown track* {track_id}")
                values.append(f"https://www.youtube.com/watch?v={track_id}")

        pages = 1 + int(len(track_ids) / SONGS_PER_PAGE)

        for page in range(pages):
            em = discord.Embed(title=f"Music queue of channel {channel.name}")
            em.set_footer(
                text=f"Currently has {len(track_ids)} song(s) | Page {page + 1}/{pages}"
            )

            for _ in range(SONGS_PER_PAGE):
                try:
                    name = names.pop(0)
                    value = values.pop(0)
                    em.add_field(
                        name=name,
                        value=value,
                        inline=INLINE,
                    )
                except IndexError:
                    break
            index.append(em)

    display = emoji_ui.NavigatorPagination(index)
    await display.send(ctx)
