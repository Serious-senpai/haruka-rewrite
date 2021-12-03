from typing import List

import asyncpg
import discord
from discord.ext import commands

from audio import MusicClient
from core import bot


@bot.command(
    name="publish",
    description="Publish the music queue of a voice channel to the bot's dashboard.\nWarning: `title` must not contain spaces.",
    usage="publish <title> <description>",
)
@commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _publish_cmd(ctx: commands.Context, title: str, *, description: str):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel: discord.abc.Connectable = ctx.author.voice.channel
    queue: List[str] = await MusicClient.queue(channel.id)

    if len(queue) < 3:
        return await ctx.send("Please add at least 3 songs to the queue to publish.")

    if len(title) > 50:
        return await ctx.send("Title must contain at most 50 characters.")

    rows: List[asyncpg.Record] = await bot.conn.fetch(f"SELECT * FROM playlist WHERE author_id = '{ctx.author.id}';")
    if len(rows) >= 10:
        return await ctx.send("You have published the maximum number of queues.")

    await bot.conn.execute(f"INSERT INTO playlist (author_id, title, description, queue, use_count) VALUES ('{ctx.author.id}', $1, $2, $3, 0);", title, description, queue)

    em: discord.Embed = discord.Embed(
        color=0x2ECC71,
    )
    em.set_author(
        name="Published music queue",
        icon_url=bot.user.avatar.url,
    )
    em.add_field(
        name="Title",
        value=title,
        inline=False,
    )
    em.add_field(
        name="Description",
        value=description,
        inline=False,
    )
    em.add_field(
        name="From channel",
        value=f"<#{channel.id}> ({len(queue)} songs)",
    )
    em.set_thumbnail(url=ctx.author.avatar.url)
    await ctx.send(embed=em)
