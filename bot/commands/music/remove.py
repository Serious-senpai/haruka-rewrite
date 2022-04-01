from typing import Union

import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import audio


@bot.command(
    name="remove",
    description="Remove a track from the current queue. Use `remove all` to remove all tracks.",
    usage="remove <track position | all | default: 1>"
)
@bot.audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _remove_cmd(ctx: Context, pos: Union[int, str] = 1):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel = ctx.author.voice.channel

    if pos == "all":
        await bot.conn.execute(f"DELETE FROM youtube WHERE id = '{channel.id}';")
        return await ctx.send(f"Removed all tracks from <#{channel.id}>")

    if not isinstance(pos, int):
        raise commands.UserInputError

    track_id = await bot.audio.remove(channel.id, pos=pos)

    if track_id is not None:
        track = await bot.audio.build(audio.PartialInvidiousSource, track_id)
        if track is None:
            embed = discord.Embed(description=f"Track ID `{track_id}`\nURL: https://www.youtube.com/watch?v={track_id}")
        else:
            embed = track.create_embed()

        embed.set_author(
            name=f"{ctx.author.name} removed 1 song from {channel.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )
        await ctx.send(embed=embed)

    else:
        await ctx.send("No song with this position.")
