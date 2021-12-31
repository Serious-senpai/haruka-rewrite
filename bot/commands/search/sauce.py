from typing import List, Optional

import discord
from discord.ext import commands

import emoji_ui
import saucenao
from core import bot


@bot.command(
    name="sauce",
    description="Find the image source with saucenao.",
    usage="sauce <URL to image>\nsauce <attachment>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _sauce_cmd(ctx: commands.Context, src: Optional[str] = None):
    if src is None:
        try:
            src = ctx.message.attachments[0].url
        except IndexError:
            raise commands.UserInputError

    results: List[saucenao.SauceResult] = await saucenao.SauceResult.get_sauce(src)
    if not results:
        return await ctx.send("Cannot find the image sauce!")

    total: int = len(results)
    embeds: List[discord.Embed] = []
    for index, result in enumerate(results):
        embed: discord.Embed = result.create_embed()
        embed.set_author(
            name="Image search result",
            icon_url=bot.user.avatar.url,
        )
        embed.set_footer(text=f"Displaying result {index + 1}/{total}")
        embeds.append(embed)

    display: emoji_ui.NavigatorPagination = emoji_ui.NavigatorPagination(embeds)
    await display.send(ctx.channel)
