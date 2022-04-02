import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

from _types import Context
from core import bot
from lib import emoji_ui, nhentai
from lib.emoji_ui import CHOICES


@bot.command(
    name="nhentai",
    aliases=["hentai"],
    description="Search for a hentai from nhentai.net from a searching query or code.\nAll 6-digit numbers are treated as codes. If no result is found with a code then it will be used as a searching query.\nThis command can only be used in a NSFW channel.",
    usage="nhentai <query or code>",
)
@commands.is_nsfw()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _nhentai_cmd(ctx: Context, *, query: str):
    hentai = None
    if nhentai.ID_PATTERN.fullmatch(query):
        hentai = await nhentai.NHentai.get(query, session=bot.session)

    if not hentai:
        if len(query) < 3:
            return await ctx.send("Searching query must have at least 3 characters")

        results = await nhentai.NHentaiSearch.search(query, session=bot.session)
        if not results:
            return await ctx.send("No matching result was found.")
        results = results[:6]

        desc = "\n".join(f"{CHOICES[index]} **{obj.id}** {escape(obj.title)}" for index, obj in enumerate(results))
        embed = discord.Embed(
            title=f"Search results for {query}",
            description=desc,
        )
        msg = await ctx.send(embed=embed)
        display = emoji_ui.SelectMenu(bot, msg, len(results))
        choice = await display.listen(ctx.author.id)

        if choice is None:
            return
        hentai = await nhentai.NHentai.get(results[choice].id, session=bot.session)

    embed = hentai.create_embed()
    embed.set_author(
        name=f"{ctx.author.name}'s request",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
    )
    await ctx.send(embed=embed)
