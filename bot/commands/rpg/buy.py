from discord.ext import commands

import game
from core import bot
from game.core import PT


@bot.command(
    name="buy",
    description="Buy an item from the shop",
    usage="buy <item ID>",
)
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _buy_cmd(ctx: commands.Context, item_id: int):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    await player.buy(ctx.channel, item_id)
