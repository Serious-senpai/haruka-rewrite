import asyncio
import gc
import logging
from typing import List, Optional

import asyncpg
import discord
from discord.ext import commands

import haruka


# uvloop does not support Windows
try:
    import uvloop
except ImportError:
    print("Unable to import uvloop, asynchronous operations will be slower.")
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


# Setup logging
class LoggingFilter(logging.Filter):

    __slots__ = ()

    def __init__(self) -> None:
        return

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "discord.player" and record.levelname == "INFO":
            return False

        return True


handler: logging.FileHandler = logging.FileHandler(filename = "./log.txt", encoding = "utf-8", mode = "a")
handler.setFormatter(logging.Formatter("HARUKA | %(levelname)s (%(name)s):: %(message)s"))
handler.addFilter(LoggingFilter())

logger: logging.Logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logger.addHandler(handler)


# Setup garbage collector
gc.enable()


async def prefix(bot, message) -> str:
    if isinstance(message.channel, discord.TextChannel):
        id: int = message.guild.id
        row: Optional[asyncpg.Record] = await bot.conn.fetchrow(f"SELECT * FROM prefix WHERE id = '{id}';")

        if not row:
            return "$"
        else:
            return row["pref"]

    else:
        return "$" # No command invoke from on_message


async def get_prefix(bot, message) -> List[str]:
    prefixes = await prefix(bot, message)
    return commands.when_mentioned_or(*prefixes)(bot, message)


# Initialize bot
intents: discord.Intents = discord.Intents.default()
intents.bans = False
intents.typing = False
intents.integrations = False
intents.invites = False
intents.webhooks = False


activity: discord.Activity = discord.Activity(
    type = discord.ActivityType.playing,
    name = "@Haruka help",
)


bot: haruka.Haruka = haruka.Haruka(
    activity = activity,
    command_prefix = get_prefix,
    intents = intents,
    case_insensitive = True,
    max_messages = 80000,
)


@bot.check
async def _blacklist_check(ctx: commands.Context):
    row: asyncpg.Record = await bot.conn.fetchrow("SELECT * FROM misc WHERE title = 'blacklist';")
    blacklist_ids: List[str] = row["id"]
    return not str(ctx.author.id) in blacklist_ids
