import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import emoji_ui, zerochan


@bot.command(
    name="zerochan",
    aliases=["zero"],
    description="Search zerochan for images",
    usage="zerochan <query>",
)
@commands.cooldown(1, 5, commands.BucketType.user)
async def _zerochan_cmd(ctx: Context, *, query: str):
    async with ctx.typing():
        urls = await zerochan.search(query, session=bot.session)

        if not urls:
            return await ctx.send("No matching result was found.")

        no_results = len(urls)
        embeds = []
        for index, url in enumerate(urls):
            embed = discord.Embed()
            embed.set_author(
                name=f"Zerochan search for {query}",
                icon_url=bot.user.avatar.url,
            )
            embed.set_image(url=url)
            embed.set_footer(text=f"Result {index + 1}/{no_results}")
            embeds.append(embed)

    display = emoji_ui.NavigatorPagination(embeds)
    await display.send(ctx.channel)
