from typing import Union

import discord
from discord.ext import commands

import image
from core import bot


@bot.command(
    name="sfw",
    aliases=["image"],
    description="Send a SFW image.\nImages from this command may not have the highest quality, use `sauce` to grab their original sources.\nPossible values for `category` are: ",  # Will be filled from help
    usage="sfw <category>",
)
@commands.cooldown(1, 4, commands.BucketType.user)
async def _sfw_cmd(ctx: commands.Context, *, category: str):
    category = category.lower()
    try:
        image_url: Union[str, discord.embeds._EmptyEmbed] = await bot.image.get(category.lower(), mode="sfw") or discord.Embed.Empty
    except image.CategoryNotFound:
        return await ctx.send(f"No category named `{category}` was found.")

    em: discord.Embed = discord.Embed(
        description=f"You can now invoke this command with `*{category.replace(' ', '_')}`",
        color=0x2ECC71,
    )
    em.set_author(
        name=f"{ctx.author.name}, this is your image!",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    em.set_image(url=image_url)

    await ctx.send(embed=em)
