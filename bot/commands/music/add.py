import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

from _types import Context
from core import bot
from lib import emoji_ui


QUEUE_MAX_SIZE = 100


@bot.command(
    name="add",
    description="Search for a YouTube track and add to queue.",
    usage="add <query>",
)
@bot.audio.in_voice()
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _add_cmd(ctx: Context, *, query: str):
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
    index = await display.listen(ctx.author.id)
    if index is None:
        return

    track = results[index]
    channel = ctx.author.voice.channel
    await bot.audio.add(channel.id, track.id)

    embed = track.create_embed()
    embed.set_author(
        name=f"{ctx.author.name} added 1 song to {channel.name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
    )
    await ctx.send(embed=embed)
