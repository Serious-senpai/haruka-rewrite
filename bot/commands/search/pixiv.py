import re
from typing import List, Optional

import discord
from discord.ext import commands

import emoji_ui
import _pixiv
from core import bot


@bot.command(
    name="pixiv",
    description="Get image(s) from Pixiv from a searching query, a URL or an ID.\nAll strings starting with `https://` are treated as URLs.\nAll 8-digit numbers are treated as IDs.\nImages from this command may not have the highest quality, use `sauce` to grab their original sources.",
    usage="pixiv <query, URL or ID>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _pixiv_cmd(ctx: commands.Context, *, query: str = ""):
    id: Optional[int] = None

    id_match: Optional[re.Match] = _pixiv.ID_PATTERN.fullmatch(query)
    if id_match:
        id: Optional[int] = int(id_match.group())

    url_match: Optional[re.Match] = re.match(r"https://", query)
    if url_match:
        match: Optional[re.Match] = _pixiv.ID_PATTERN.search(query)
        if match:
            id: Optional[int] = int(match.group())
        else:
            return await ctx.send("Invalid URL.")

    if id:
        # A URL or an ID was entered
        async with ctx.typing():
            artwork: _pixiv.PixivArtwork = await _pixiv.PixivArtwork.from_id(id)

            if not artwork:
                return await ctx.send("Cannot find any artworks with this ID!")

            if isinstance(ctx.channel, discord.TextChannel):
                if artwork.nsfw and not ctx.channel.is_nsfw():
                    return await ctx.send("🔞 This artwork is NSFW and can only be shown in a NSFW channel!")

            return await ctx.send(embed=await artwork.create_embed())

    # Search Pixiv by query
    if len(query) < 2:
        return await ctx.send("Search query must have at least 2 characters")

    rslt: List[_pixiv.PixivArtwork] = await _pixiv.PixivArtwork.search(query)
    if not rslt:
        return await ctx.send("No matching results found.")

    index: List[discord.Embed] = []
    async with ctx.typing():
        for i, artwork in enumerate(rslt[:6]):
            em: discord.Embed = await artwork.create_embed()
            em.set_footer(text=f"Displaying result #{i + 1}")
            em.set_author(
                name=f"{ctx.author.name} searched for {query}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
            )
            index.append(em)

    display: emoji_ui.Pagination = emoji_ui.Pagination(index)
    await display.send(ctx.channel)
