from typing import List, Optional

import discord
from discord.ext import commands

import emoji_ui
from audio import *
from core import bot
from emoji_ui import CHOICES


QUEUE_MAX_SIZE: int = 100


@bot.command(
    name = "add",
    description = "Search for a YouTube track and add to queue.",
    usage = "add <query>",
)
@commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _add_cmd(ctx: commands.Context, *, query):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel: discord.abc.Connectable = ctx.author.voice.channel

    track_ids: List[str] = await MusicClient.queue(channel.id)
    if len(track_ids) >= QUEUE_MAX_SIZE:
        return await ctx.send(f"The music queue for this channel has reached its maximum size ({QUEUE_MAX_SIZE} limit).")

    tracks: List[PartialInvidiousSource] = await PartialInvidiousSource.search(query)

    if tracks:
        em: discord.Embed = discord.Embed(
            title = f"Search results for {query}",
            color = 0x2ECC71,
        )
        em.set_author(
            name = f"{ctx.author.name}'s song request",
            icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
        em.set_footer(text = "This message will expire after 5 minutes.")
        for index, track in enumerate(tracks):
            em.add_field(
                name = f"{CHOICES[index]} {track.title}",
                value = track.channel,
                inline = False,
            )
        msg: discord.Message = await ctx.send(embed = em)

    else:
        return await ctx.send(f"No matching result for {query}")

    display: emoji_ui.SelectMenu = emoji_ui.SelectMenu(msg, len(tracks))
    choice: Optional[int] = await display.listen(ctx.author.id)

    if choice is not None:
        # If it's searchable then it must be available
        track: PartialInvidiousSource = await PartialInvidiousSource.build(tracks[choice].id)
    else:
        return

    await MusicClient.add(channel.id, track.id)

    em: discord.Embed = track.create_embed()
    em.set_author(
        name = f"{ctx.author.name} added 1 song to {channel.name}",
        icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    await ctx.send(embed = em)
