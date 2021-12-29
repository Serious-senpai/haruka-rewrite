from discord.ext import commands

import game
from core import bot
from game.core import PT


@bot.command(
    name="battle",
    description="Initiate a battle in the current location",
)
@game.rpg_check()
@commands.cooldown(1, 10, commands.BucketType.user)
async def _battle_cmd(ctx: commands.Context):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    await player.battle(ctx.channel)
