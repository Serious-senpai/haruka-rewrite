from typing import Optional, Type

from discord.ext import commands

import game
import utils
from core import bot
from game.core import LT, PT


@bot.command(
    name="teleport",
    aliases=["tp"],
    description="Teleport to another location",
    usage="teleport <location ID>",
)
@utils.testing()
@game.rpg_check()
@commands.cooldown(1, 3, commands.BucketType.user)
async def _teleport_cmd(ctx: commands.Context, location_id: int):
    player: PT = await game.BasePlayer.from_user(ctx.author)
    destination: Optional[Type[LT]] = player.world.get_location(location_id)
    if destination is None:
        return await ctx.send(f"Cannot find any locations with `ID {location_id}`!")

    try:
        device: Type[game.TeleportDevice] = player.get_item(5)
        await device.effect(player, ctx.channel, destination)
    except game.ItemNotFound:
        return await ctx.send("You don't have any Teleport Devices!")
