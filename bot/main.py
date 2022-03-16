from __future__ import annotations

from core import bot
from events import *
from commands import *
import asyncio
import os
import sys
import tracemalloc
from typing import TYPE_CHECKING


tracemalloc.start()  # noqa
print(f"Running on {sys.platform}\nPython {sys.version}")
with open("./bot/assets/server/log.txt", "w") as f:
    f.write(f"HARUKA BOT\nRunning on Python {sys.version}\n" + "-" * 50 + "\n")


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
if not os.path.isdir("./bot/assets/server/images"):
    os.mkdir("./bot/assets/server/images")


async def runner(bot: haruka.Haruka) -> None:
    try:
        await bot.start()
    except KeyboardInterrupt:
        return


asyncio.run(runner(bot))
