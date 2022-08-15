import asyncio
import gc
import logging
import os
import sys
import traceback
import tracemalloc
from typing import Any, List

import discord
from discord.ext import commands

import haruka
from _types import Context
from lib import trees


# uvloop does not support Windows
try:
    import uvloop
except ImportError:
    print("Unable to import uvloop, asynchronous operations will be slower.")
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


tracemalloc.start()  # noqa
print(f"Running on {sys.platform}\nPython {sys.version}")


# YouTube tracks information
if not os.path.isdir("./tracks"):
    os.mkdir("./tracks")


# Server resources at runtime
if not os.path.isdir("./server"):
    os.mkdir("./server")
if not os.path.isdir("./server/images"):
    os.mkdir("./server/images")
if not os.path.isdir("./server/audio"):
    os.mkdir("./server/audio")


# Assets at runtime
if not os.path.isdir("./bot/web/assets"):
    os.mkdir("./bot/web/assets")
if not os.path.isdir("./bot/web/assets/images"):
    os.mkdir("./bot/web/assets/images")


with open("./bot/web/assets/log.txt", "w") as f:
    f.write(f"HARUKA BOT\nRunning on Python {sys.version}\n" + "-" * 50 + "\n")


# Setup logging
DEBUG_MODE = False


class LoggingFilter(logging.Filter):

    __slots__ = ()

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "discord.player" and record.levelname == "INFO":
            return False

        return True


handler = logging.FileHandler(filename="./bot/web/assets/log.txt", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s %(message)s"))
handler.addFilter(LoggingFilter())

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
logger.addHandler(handler)


# Setup garbage collector
gc.enable()


# Set default attributes for all embeds
class Embed(discord.Embed):
    def __init__(self, *args, **kwargs) -> None:
        self.timestamp = discord.utils.utcnow()
        super().__init__(*args, **kwargs)
        if not self.colour:
            self.colour = discord.Colour(0x2ECC71)


discord.Embed = Embed  # type: ignore


async def prefix(bot: haruka.Haruka, message: discord.Message) -> str:
    if message.guild:
        id = message.guild.id
        row = await bot.conn.fetchrow(f"SELECT * FROM prefix WHERE id = '{id}';")

        if not row:
            return "$"
        else:
            return row["pref"]

    else:
        return "$"


async def get_prefix(bot: haruka.Haruka, message: discord.Message) -> List[str]:
    prefixes = await prefix(bot, message)
    return commands.when_mentioned_or(*prefixes)(bot, message)


# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.bans = False
intents.typing = False
intents.integrations = False
intents.invites = False
intents.webhooks = False


bot = haruka.Haruka(
    activity=discord.Game("Restarting..."),
    command_prefix=get_prefix,
    intents=intents,
    case_insensitive=True,
    strip_after_prefix=True,
    max_messages=5000,
    enable_debug_events=DEBUG_MODE,
    tree_cls=trees.SlashCommandTree,
)


@bot.check
async def _blacklist_check(ctx: Context) -> bool:
    row = await bot.conn.fetchrow(f"SELECT * FROM blacklist WHERE id = '{ctx.author.id}';")
    return row is None


@bot.before_invoke
async def _before_invoke(ctx: Context) -> None:
    # Count text commands
    if ctx.command.root_parent:
        return

    if await bot.is_owner(ctx.author):
        return

    name = ctx.command.name
    if name not in bot._command_count:
        bot._command_count[name] = []

    bot._command_count[name].append(ctx)


@bot.event
async def on_ready() -> None:
    bot.log(f"Logged in as {bot.user}")
    print(f"Logged in as {bot.user}")


@bot.event
async def on_error(event_method: str, *args: Any, **kwargs: Any) -> None:
    exc_type, _, _ = sys.exc_info()
    if issubclass(exc_type, discord.Forbidden):  # type: ignore
        return

    bot.log(f"Exception in {event_method}:")
    bot.log(traceback.format_exc())
    await bot.report("An error has just occurred and was handled by `on_error`", send_state=False)
