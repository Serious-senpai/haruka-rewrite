from discord.ext import commands

import game
import utils
from core import bot
from game.player import PT


@bot.command(
    name="class",
    description="Change your character's class. You must be at a certain location to perform this action.",
)
@utils.testing()
@game.rpg_check()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _class_cmd(ctx: commands.Context):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    await player.change_class(ctx.channel)
