import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import audio, emoji_ui


SONGS_PER_PAGE = 8


@bot.command(
    name="queue",
    description="View the music queue of a voice channel"
)
@bot.audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _queue_cmd(ctx: Context):
    channel = ctx.author.voice.channel
    track_ids = await bot.audio.queue(channel.id)
    pages = 1 + len(track_ids) // SONGS_PER_PAGE

    counter = 0
    embeds = []

    async with ctx.typing():
        for page in range(pages):
            embed = discord.Embed()
            embed.set_author(
                name=f"Music queue of channel {channel.name}",
                icon_url=bot.user.avatar.url,
            )
            embed.set_footer(text=f"Currently has {len(track_ids)} song(s) | Page {page + 1}/{pages}")

            for _ in range(SONGS_PER_PAGE):
                try:
                    track_id = track_ids[counter]
                    track = await bot.audio.build(audio.PartialInvidiousSource, track_id)
                except IndexError:
                    break

                counter += 1
                if track is None:
                    embed.add_field(
                        name=f"**#{counter}** <Track ID={track_id}>",
                        value=f"https://www.youtube.com/watch?v={track_id}",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name=f"**#{counter}** {track.title}",
                        value=track.channel,
                        inline=False,
                    )

            embeds.append(embed)

    display = emoji_ui.NavigatorPagination(bot, embeds)
    await display.send(ctx)
