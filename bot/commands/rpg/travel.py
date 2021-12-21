from typing import Optional

from discord.ext import commands

import game
import utils
from core import bot
from game.core import LT, PT


@bot.command(
    name="travel",
    description="Travel to a location of the same world. You can get a list of location IDs from `world`",
    usage="travel <location ID>",
)
@utils.testing()
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _travel_cmd(ctx: commands.Context, wid: int):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    location: Optional[LT] = player.world.get_location(wid)
    await player.travel_to(ctx.channel, location)
