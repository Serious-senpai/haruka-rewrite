import random

from discord.ext import commands

import utils
from _types import Context
from core import bot


exceptions = tuple(utils.get_all_subclasses(Exception))


@bot.command(
    name="raise",
    description="Raise a random exception",
)
@commands.is_owner()
async def _raise_cmd(ctx: Context):
    exc = random.choice(exceptions)
    raise exc
