from typing import Optional

from discord.ext import commands

import game
from core import bot
from game.core import LT, PT


@bot.command(
    name="location",
    description="View information about a location",
    usage="location <location ID | default: the one you are in>",
)
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _location_cmd(ctx: commands.Context, id: int = None):
    player: PT = await game.BasePlayer.from_user(ctx.author)

    location: Optional[LT]
    if id is None:
        location = player.location
    else:
        location = player.world.get_location(id)

    if location is None:
        return await ctx.send(f"Cannot find any locations with `ID {id}`!")
    await ctx.send(embed=player.map_location(location))
