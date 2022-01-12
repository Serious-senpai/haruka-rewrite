from typing import List

import discord
from discord.ext import commands

import _danbooru
import emoji_ui
from core import bot


@bot.command(
    name="danbooru",
    aliases=["dan"],
    description="Search danbooru for images",
    usage="danbooru <query>",
)
@commands.is_nsfw()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _danbooru_cmd(ctx: commands.Context, *, query: str):
    async with ctx.typing():
        urls: List[str] = await _danbooru.search(query)

        if not urls:
            return await ctx.send("No matching result was found.")

        no_results: int = len(urls)
        embeds: List[discord.Embed] = []
        for index, url in enumerate(urls):
            embed: discord.Embed = discord.Embed()
            embed.set_author(
                name=f"Danbooru search for {query}",
                icon_url=bot.user.avatar.url,
            )
            embed.set_image(url=url)
            embed.set_footer(text=f"Result {index + 1}/{no_results}")
            embeds.append(embed)

    display: emoji_ui.NavigatorPagination = emoji_ui.NavigatorPagination(embeds)
    await display.send(ctx.channel)
