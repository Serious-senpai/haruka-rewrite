from discord.ext import commands

import game
from core import bot
from game.core import PT


@bot.command(
    name="inventory",
    aliases=["inv"],
    description="View your inventory",
)
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _inventory_cmd(ctx: commands.Context):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    await player.send_inventory(ctx.channel)
