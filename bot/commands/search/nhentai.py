from typing import List, Optional

import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import emoji_ui
import _nhentai
from core import bot
from emoji_ui import CHOICES
from leech import search_nhentai, get_nhentai


@bot.command(
    name="nhentai",
    aliases=["hentai"],
    description="Search for a hentai from nhentai.net from a searching query or code.\nAll 6-digit numbers are treated as codes. If no result is found with a code then it will be used as a searching query.\nThis command can only be used in a NSFW channel.",
    usage="nhentai <query or code>",
)
@commands.is_nsfw()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _nhentai_cmd(ctx: commands.Context, *, query: str):
    try:
        id: int = int(query)
        hentai: Optional[_nhentai.NHentai] = await get_nhentai(id)
        if not hentai:
            raise ValueError

    except ValueError:
        if len(query) < 3:
            return await ctx.send("Searching query must have at least 3 characters")

        rslt: Optional[List[_nhentai.NHentaiSearch]] = await search_nhentai(query)
        if not rslt:
            return await ctx.send("No matching result was found.")
        rslt = rslt[:6]

        desc: str = "\n".join(f"{CHOICES[index]} **{obj.id}** {obj.title}" for index, obj in enumerate(rslt))
        em: discord.Embed = discord.Embed(
            title=f"Search results for {query}",
            description=escape(desc),
            color=0x2ECC71,
        )
        msg: discord.Message = await ctx.send(embed=em)
        display: emoji_ui.SelectMenu = emoji_ui.SelectMenu(msg, len(rslt))
        choice: Optional[int] = await display.listen(ctx.author.id)
        if choice is not None:
            hentai: _nhentai.NHentai = await get_nhentai(rslt[choice].id)

    em: discord.Embed = hentai.create_embed()
    em.set_author(
        name=f"{ctx.author.name}'s request",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    await ctx.send(embed=em)
