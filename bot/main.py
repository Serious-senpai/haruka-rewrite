import asyncio
import os
import sys
import tracemalloc


tracemalloc.start()  # noqa
with open("./bot/assets/server/log.txt", "w") as f:
    f.write(f"HARUKA BOT\nRunning on Python {sys.version}\n" + "-" * 50 + "\n")


from commands import *
from events import *
from core import bot


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


print(f"Running on {sys.platform}\nPython {sys.version}")
bot.loop = asyncio.get_event_loop()
try:
    bot.loop.run_until_complete(bot.start())
except KeyboardInterrupt:
    bot.loop.run_until_complete(asyncio.shield(bot.close()))
