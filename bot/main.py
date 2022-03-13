import asyncio
import sys
import tracemalloc

tracemalloc.start()  # noqa
with open("./log.txt", "w") as f:
    f.write(f"HARUKA BOT\nRunning on Python {sys.version}\n" + "-" * 50 + "\n")

from commands import *
from events import *
from core import bot


print(f"Running on {sys.platform}\nPython {sys.version}")
bot.loop = asyncio.get_event_loop()
try:
    bot.loop.run_until_complete(bot.start())
except KeyboardInterrupt:
    bot.loop.run_until_complete(asyncio.shield(bot.close()))
