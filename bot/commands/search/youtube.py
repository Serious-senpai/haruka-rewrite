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

    async with ctx.typing():
        source = await audio.embed_search(query, ctx.channel, ctx.author.id)
        if not source:
            return

        embed = audio.create_audio_embed(source)
        with utils.TimingContextManager() as measure:
            url = await audio.fetch(source)

        if url is not None:
            embed.set_footer(text=f"Fetched data in {utils.format(measure.result)}")
            button = discord.ui.Button(style=discord.ButtonStyle.link, url=url, label="Audio URL")
            view = discord.ui.View()
            view.add_item(button)

            await ctx.send(embed=embed, view=view)

        else:
            embed.set_footer(text="Cannot fetch this track")
            embed.remove_field(-1)
            await ctx.send(embed=embed)
