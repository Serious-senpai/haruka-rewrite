from discord.ext import commands

import game
import utils
from core import bot
from game.core import PT


@bot.command(
    name="use",
    description="Use an item in your inventory",
    usage="use <item ID>",
)
@utils.testing()
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _use_cmd(ctx: commands.Context, item_id: int):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    await player.use(ctx.channel, item_id)
