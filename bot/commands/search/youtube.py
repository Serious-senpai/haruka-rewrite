import time
from typing import Optional

import discord
from discord.ext import commands

import audio
from core import bot


@bot.command(
    name="youtube",
    aliases=["yt"],
    description="Search for a YouTube video and get the mp3 file.\nMaximum file size is 8 MB regardless of the server's upload limit.",
    usage="youtube <query>",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def _youtube_cmd(ctx: commands.Context, *, query: str):
    if len(query) < 3:
        return await ctx.send("Search query must have at least 3 characters")

    source: Optional[audio.InvidiousSource] = await audio.embed_search(query, ctx.channel, ctx.author.id)
    if not source:
        return

    em: discord.Embed = source.create_embed()
    em.set_author(
        name=f"{ctx.author.name}'s request",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )

    async with ctx.typing():
        t: float = time.perf_counter()
        url: Optional[str] = await audio.fetch(source.id)
        done: float = time.perf_counter() - t

        if not url:
            em.set_footer(text="Cannot fetch video file")
            return await ctx.send(embed=em)

        em.add_field(
            name="Video URL",
            value=f"[Download]({url})",
            inline=False,
        )
        em.set_footer(text="Fetched data in {:.2f} ms.".format(1000 * done))
        await ctx.send(embed=em)
