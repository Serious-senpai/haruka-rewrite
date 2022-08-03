from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING


import env
from core import bot
from events import *
from commands import *
if TYPE_CHECKING:
    import haruka


# YouTube tracks information
if not os.path.exists("./tracks"):
    os.mkdir("./tracks")


# Server resources at runtime
if not os.path.exists("./server"):
    os.mkdir("./server")
if not os.path.exists("./server/images"):
    os.mkdir("./server/images")
if not os.path.exists("./server/audio"):
    os.mkdir("./server/audio")


# Assets at runtime
if not os.path.isdir("./bot/web/assets/images"):
    os.mkdir("./bot/web/assets/images")


async def runner(bot: haruka.Haruka) -> None:
    try:
        await bot.start(env.TOKEN)
    except KeyboardInterrupt:
        return


if env.BUILD_CHECK:
    print("Check success")
else:
    asyncio.run(runner(bot))
