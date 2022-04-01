import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import image


@bot.command(
    name="sfw",
    description="Send a SFW image.\nImages from this command may not have the highest quality, use `{prefix}sauce` to grab their original sources.\nPossible values for `category` are: ",  # Will be filled from help
    usage="sfw <category>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _sfw_cmd(ctx: Context, *, category: str):
    category = category.lower()
    try:
        image_url = await bot.image.get(category.lower(), mode="sfw")
    except image.CategoryNotFound:
        return await ctx.send(f"No category named `{category}` was found.")

    embed = discord.Embed()
    embed.set_author(
        name=f"{ctx.author.name}, this is your image!",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
    )
    embed.set_image(url=image_url)

    await ctx.send(embed=embed)
