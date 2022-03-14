import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="image",
    description="Get an image from the bot's internal images collection",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _image_cmd(ctx: Context):
    image_url = bot.asset_client.get_anime_image()
    if image_url is None:
        return await ctx.send("The internal images collection is temporarily unavailable.")

    embed = discord.Embed()
    embed.set_author(
        name=f"{ctx.author.name}, this is your image!",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
    )
    embed.set_image(url=image_url)

    await ctx.send(embed=embed)
