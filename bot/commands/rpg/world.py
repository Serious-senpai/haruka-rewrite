from discord.ext import commands

import game
from core import bot
from game.core import PT


@bot.command(
    name="world",
    aliases=["map"],
    description="View the current world you are in",
)
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _world_cmd(ctx: commands.Context):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    await ctx.send(embed=player.map_world())
