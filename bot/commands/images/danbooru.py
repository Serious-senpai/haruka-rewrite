import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import danbooru, emoji_ui


@bot.command(
    name="danbooru",
    aliases=["dan"],
    description="Search danbooru for images",
    usage="danbooru <query>",
)
@commands.is_nsfw()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _danbooru_cmd(ctx: Context, *, query: str):
    async with ctx.typing():
        urls = await danbooru.search(query)

        if not urls:
            return await ctx.send("No matching result was found.")

        no_results = len(urls)
        embeds = []
        for index, url in enumerate(urls):
            embed = discord.Embed()
            embed.set_author(
                name=f"Danbooru search for {query}",
                icon_url=bot.user.avatar.url,
            )
            embed.set_image(url=url)
            embed.set_footer(text=f"Result {index + 1}/{no_results}")
            embeds.append(embed)

    display = emoji_ui.NavigatorPagination(bot, embeds)
    await display.send(ctx.channel)
