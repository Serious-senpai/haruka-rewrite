import discord
from discord.ext import commands

import audio
from core import bot


QUEUE_MAX_SIZE = 100


@bot.command(
    name="add",
    description="Search for a YouTube track and add to queue.",
    usage="add <query>",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _add_cmd(ctx: commands.Context, *, query: str):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel = ctx.author.voice.channel

    track_ids = await audio.MusicClient.queue(channel.id)
    if len(track_ids) >= QUEUE_MAX_SIZE:
        return await ctx.send(f"The music queue for this channel has reached its maximum size ({QUEUE_MAX_SIZE} limit).")

    track = await audio.embed_search(query, ctx.channel, ctx.author.id)
    if not track:
        return

    await audio.MusicClient.add(channel.id, track.id)

    embed = track.create_embed()
    embed.set_author(
        name=f"{ctx.author.name} added 1 song to {channel.name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    await ctx.send(embed=embed)
