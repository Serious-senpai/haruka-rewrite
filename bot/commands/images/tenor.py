import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import emoji_ui, tenor


@bot.command(
    name="tenor",
    description="Search tenor for images",
    usage="tenor <query>",
)
@commands.cooldown(1, 3, commands.BucketType.user)
async def _tenor_cmd(ctx: Context, *, query: str):
    urls = await tenor.search(query, session=bot.session)

    if not urls:
        return await ctx.send("No matching result was found.")

    no_results = len(urls)
    embeds = []
    for index, url in enumerate(urls):
        embed = discord.Embed()
        embed.set_author(
            name=f"Tenor search for {query}",
            icon_url=bot.user.avatar.url,
        )
        embed.set_image(url=url)
        embed.set_footer(text=f"Result {index + 1}/{no_results}")
        embeds.append(embed)

    display = emoji_ui.NavigatorPagination(bot, embeds)
    await display.send(ctx.channel)
