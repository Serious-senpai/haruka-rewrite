import discord
from discord.ext import commands

import game
import utils
from core import bot
from game.core import PT


@bot.command(
    name="account",
    aliases=["acc"],
    description="View a user's RPG game account information",
    usage="account <user | default: yourself>"
)
@utils.testing()
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _account_cmd(ctx: commands.Context, user: discord.User = None):
    if user is None:
        user = ctx.author

    player: PT = await game.BasePlayer.from_user(user)
    await ctx.send(embed=player.create_embed())
