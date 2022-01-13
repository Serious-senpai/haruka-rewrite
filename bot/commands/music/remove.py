from typing import Union

import discord
from discord.ext import commands

import audio
from core import bot


@bot.command(
    name="remove",
    description="Remove a track from the current queue. Use `remove all` to remove all tracks.",
    usage="remove <track position | all | default: 1>"
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _remove_cmd(ctx: commands.Context, pos: Union[int, str] = 1):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel = ctx.author.voice.channel

    if pos == "all":
        await bot.conn.execute(f"DELETE FROM youtube WHERE id = '{channel.id}';")
        return await ctx.send(f"Removed all tracks from <#{channel.id}>")

    if not isinstance(pos, int):
        raise commands.UserInputError

    id = await audio.MusicClient.remove(channel.id, pos=pos)

    if id is not None:
        track = await audio.InvidiousSource.build(id)
        embed = track.create_embed()
        embed.set_author(
            name=f"{ctx.author.name} removed 1 song from {channel.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("No song with this position.")
