from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING


import env
from core import bot
from events import *
from commands import *
if TYPE_CHECKING:
    import haruka


async def runner(bot: haruka.Haruka) -> None:
    try:
        await bot.start(env.TOKEN)
    except KeyboardInterrupt:
        return


if env.BUILD_CHECK:
    print("Check success")
else:
    asyncio.run(runner(bot))
