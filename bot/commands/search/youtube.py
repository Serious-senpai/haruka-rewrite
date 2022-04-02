import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

from _types import Context
from core import bot
from lib import audio, emoji_ui, emojis, utils


@bot.command(
    name="youtube",
    aliases=["yt"],
    description="Search for a YouTube video and get the mp3 file.",
    usage="youtube <query>",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def _youtube_cmd(ctx: Context, *, query: str):
    if len(query) < 3:
        return await ctx.send("Search query must have at least 3 characters")

    results = await bot.audio.search(query)
    if not results:
        return await ctx.send("No matching result was found.")

    embed = discord.Embed()
    embed.set_author(name=f"Search results for {query[:50]}", icon_url=bot.user.avatar.url)
    for index, result in enumerate(results):
        embed.add_field(
            name=f"{emoji_ui.CHOICES[index]} {escape(result.title)}",
            value=escape(result.channel),
            inline=False,
        )

    message = await ctx.send(embed=embed)
    display = emoji_ui.SelectMenu(bot, message, len(results))
    track_index = await display.listen(ctx.author.id)

    if track_index is None:
        return

    track = await bot.audio.build(audio.InvidiousSource, results[track_index].id)
    if track is None:
        return await ctx.send(f"{emojis.MIKUCRY} Cannot gather information about this video!")

    async with ctx.typing():
        with utils.TimingContextManager() as measure:
            url = await bot.audio.fetch(track)

    if not url:
        return await ctx.send(f"{emojis.MIKUCRY} Cannot fetch audio for this video!")

    embed = bot.audio.create_audio_embed(track)
    embed.set_footer(text=f"Fetched audio in {utils.format(measure.result)}")
    await ctx.send(embed=embed)
