import discord
from discord.ext import commands

import image
from core import bot


@bot.command(
    name="nsfw",
    description="Send a NSFW image.\nImages from this command may not have the highest quality, use `{prefix}sauce` to grab their original sources.\nPossible values for `category` are: ",  # Will be filled from help
    usage="nsfw <category>",
)
@commands.is_nsfw()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _nsfw_cmd(ctx: commands.Context, *, category: str):
    category = category.lower()
    try:
        image_url = await bot.image.get(category, mode="nsfw") or discord.Embed.Empty
    except image.CategoryNotFound:
        return await ctx.send(f"No category named `{category}` was found.")

    embed = discord.Embed(description="Check out this [Android app](https://github.com/Saratoga-CV6/waifu-generator/releases) to view images directly on your phone!")
    embed.set_author(
        name=f"{ctx.author.name}, this is your image!",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    embed.set_image(url=image_url)

    await ctx.send(embed=embed)
