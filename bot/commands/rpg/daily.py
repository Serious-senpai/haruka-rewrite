import discord
from discord.ext import commands

import game
from core import bot, prefix
from game.core import PT


DAILY_REWARD: int = 300


@bot.command(
    name="daily",
    description="Claim your daily reward",
)
@commands.cooldown(1, 86400, commands.BucketType.user)
async def _daily_cmd(ctx: commands.Context):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    if not player:
        player = await game.BasePlayer.make_new(ctx.author)
        pref: str = await prefix(bot, ctx.message)
        embed: discord.Embed = discord.Embed(description=f"It looks like this is the first time you have played this game. Here are some commands to help you get started!\nYou can still use `{pref}help <command>` to get help as usual.\n\nYou are currently in school, use `{pref}travel 0` to go back home!")
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
            value=f"`{pref}world` or `{pref}map`",
            inline=False,
        )
        embed.add_field(
            name="Travel to a location",
            value=f"`{pref}travel <location ID>`",
            inline=False,
        )
        embed.add_field(
            name="How to get isekai'd?",
            value="You will be transfered to another world if ~~you get hit by truck-kun~~ your HP reaches 0",
            inline=False,
        )

        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty)
        await ctx.send(embed=embed)

    await bot.conn.execute(f"UPDATE rpg SET money = money + {DAILY_REWARD} WHERE id = '{ctx.author.id}';")
    await ctx.send(f"Claimed `💲{DAILY_REWARD}` daily reward!")
