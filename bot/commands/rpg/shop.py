from discord.ext import commands

import game
from core import bot
from game.core import PT


@bot.command(
    name="shop",
    description="View the shop at your current location",
)
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _shop_cmd(ctx: commands.Context):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    await player.send_shop(ctx.channel)
