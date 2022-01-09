from typing import List, Optional

import discord
from discord.ext import commands

import audio
import emoji_ui
from core import bot


SONGS_PER_PAGE: int = 8
INLINE: bool = False


@bot.command(
    name="queue",
    description="View the music queue of a voice channel"
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _queue_cmd(ctx: commands.Context):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel: discord.abc.Connectable = ctx.author.voice.channel
    track_ids: List[str] = await audio.MusicClient.queue(channel.id)

    names: List[str] = []
    values: List[str] = []
    index: List[discord.Embed] = []

    async with ctx.typing():
        for _index, track_id in enumerate(track_ids):
            track: Optional[audio.PartialInvidiousSource] = await audio.PartialInvidiousSource.build(track_id)
            if track:
                names.append(f"**#{_index + 1}** {track.title}")
                values.append(track.channel)
            else:
                names.append(f"**#{_index + 1}** *Unknown track* {track_id}")
                values.append(f"https://www.youtube.com/watch?v={track_id}")

        pages: int = 1 + int(len(track_ids) / SONGS_PER_PAGE)

        for page in range(pages):
            em: discord.Embed = discord.Embed(title=f"Music queue of channel {channel.name}")
            em.set_footer(
                text=f"Currently has {len(track_ids)} song(s) | Page {page + 1}/{pages}"
            )

            for _ in range(SONGS_PER_PAGE):
                try:
                    name: str = names.pop(0)
                    value: str = values.pop(0)
                    em.add_field(
                        name=name,
                        value=value,
                        inline=INLINE,
                    )
                except IndexError:
                    break
            index.append(em)

    display: emoji_ui.NavigatorPagination = emoji_ui.NavigatorPagination(index)
    await display.send(ctx)
