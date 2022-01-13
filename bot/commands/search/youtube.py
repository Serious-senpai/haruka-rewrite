import discord
from discord.ext import commands

import audio
import utils
from core import bot


@bot.command(
    name="youtube",
    aliases=["yt"],
    description="Search for a YouTube video and get the mp3 file.",
    usage="youtube <query>",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def _youtube_cmd(ctx: commands.Context, *, query: str):
    if len(query) < 3:
        return await ctx.send("Search query must have at least 3 characters")

    source = await audio.embed_search(query, ctx.channel, ctx.author.id)
    if not source:
        return

    em = source.create_embed()
    em.set_author(
        name=f"{ctx.author.name}'s request",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )

    async with ctx.typing():
        with utils.TimingContextManager() as measure:
            url = await audio.fetch(source)

        if not url:
            em.set_footer(text="Cannot fetch audio file")
            return await ctx.send(embed=em)

        em.add_field(
            name="Audio URL",
            value=f"[Download]({url})",
            inline=False,
        )
        em.set_footer(text=f"Fetched data in {utils.format(measure.result)}")
        await ctx.send(embed=em)
