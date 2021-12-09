import random
from typing import Tuple

from discord.ext import commands

from core import bot


exceptions: Tuple[BaseException, ...] = (
    Exception,
    TypeError,
    ValueError,
    RuntimeError,
    NotImplementedError,
)


@bot.command(
    name="raise",
    description="Raise a random exception",
)
@commands.is_owner()
async def _raise_cmd(ctx: commands.Context):
    raise random.choice(exceptions)
