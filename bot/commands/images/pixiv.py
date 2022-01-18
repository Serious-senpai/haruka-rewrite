import discord
from discord.ext import commands

import emoji_ui
import _pixiv
from core import bot


@bot.command(
    name="pixiv",
    description="Get image(s) from Pixiv from a searching query, a URL or an ID.\nAll strings starting with `https://` are treated as URLs.\nImages from this command may not have the highest quality, use `{0}sauce` to grab their original sources.",
    usage="pixiv <query, URL or ID>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _pixiv_cmd(ctx: commands.Context, *, query: str = ""):
    async with ctx.typing():
        parsed = await _pixiv.parse(query, session=bot.session)
        if isinstance(parsed, _pixiv.PixivArtwork):
            return await ctx.send(embed=await parsed.create_embed(session=bot.session))

        if not parsed:
            return await ctx.send("No matching result was found.")

        embeds = []
        for index, artwork in enumerate(parsed[:6]):
            embed = await artwork.create_embed(session=bot.session)
            embed.set_footer(text=f"Displaying result #{index + 1}")
            embed.set_author(
                name=f"{ctx.author.name} searched for {query}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
            )
            embeds.append(embed)

    display = emoji_ui.Pagination(embeds)
    await display.send(ctx.channel)
