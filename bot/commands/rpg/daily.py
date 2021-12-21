import discord
from discord.ext import commands

import game
import utils
from core import bot, prefix
from game.core import PT


DAILY_REWARD: int = 300


@bot.command(
    name="daily",
    description="Claim your daily reward",
)
@utils.testing()
@commands.cooldown(1, 86400, commands.BucketType.user)
async def _daily_cmd(ctx: commands.Context):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    if not player:
        player = await game.BasePlayer.make_new(ctx.author)
        pref: str = await prefix(bot, ctx.message)
        embed: discord.Embed = discord.Embed(
            description="It looks like this is the first time you have played this game. Here are some commands to help you get started!",
            color=0x2ECC71,
        )
        embed.set_author(
            name="Game Tutorial",
            icon_url=bot.user.avatar.url,
        )
        embed.add_field(
            name="View your status",
            value=f"`{pref}account` or `{pref}acc`",
            inline=False,
        )
        embed.add_field(
            name="View locations you can travel to",
            value=f"`{pref}world`",
            inline=False,
        )
        embed.add_field(
            name="Travel to a location",
            value=f"`{pref}travel <location ID>`",
            inline=False,
        )

        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty)
        await ctx.send(embed=embed)

    player.money += DAILY_REWARD
    await player.update()
    await ctx.send(f"Claimed `💲{DAILY_REWARD}` daily reward!")
