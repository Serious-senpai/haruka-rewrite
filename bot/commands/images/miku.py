import discord
from discord.ext import commands

import leech
from core import bot


@bot.command(
    name="miku",
    description="HATSUNE MIKU NUMBER ONE!\nImages from this command may not have the highest quality, use `{0}sauce` to grab their original sources.",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _miku_cmd(ctx: commands.Context):
    return await ctx.send("This command is deprecated.")
    image_url: str = leech.get_miku()
    em: discord.Embed = discord.Embed()
    em.set_author(
        name=f"{ctx.author.name} simped Miku!",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    em.set_image(url=image_url)
    await ctx.send(embed=em)
