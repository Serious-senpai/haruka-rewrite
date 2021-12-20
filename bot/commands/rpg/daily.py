from discord.ext import commands

import utils
from core import bot


@bot.command(
    name="daily",
    description="Claim your daily reward",
)
@utils.testing()
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx: commands.Context):
    ...
