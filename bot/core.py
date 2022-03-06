import asyncio
import gc
import logging
from typing import List

import discord
from discord.ext import commands

import haruka
from _types import Context


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


handler = logging.FileHandler(filename="./log.txt", encoding="utf-8", mode="a")
handler.setFormatter(logging.Formatter("HARUKA | %(levelname)s (%(name)s):: %(message)s"))
handler.addFilter(LoggingFilter())

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logger.addHandler(handler)


# Setup garbage collector
gc.enable()


# Set default attributes for all embeds
class Embed(discord.Embed):
    def __init__(self, *args, **kwargs) -> None:
        self.timestamp = discord.utils.utcnow()
        super().__init__(*args, **kwargs)
        if not self.colour:
            self.colour = 0x2ECC71


discord.Embed = Embed


async def prefix(bot: haruka.Haruka, message: discord.Message) -> str:
    if isinstance(message.channel, discord.TextChannel):
        id = message.guild.id
        row = await bot.conn.fetchrow(f"SELECT * FROM prefix WHERE id = '{id}';")

        if not row:
            return "$"
        else:
            return row["pref"]

    else:
        return "$"


async def get_prefix(bot, message) -> List[str]:
    prefixes = await prefix(bot, message)
    return commands.when_mentioned_or(*prefixes)(bot, message)


# Initialize bot
intents = discord.Intents.default()
intents.bans = False
intents.typing = False
intents.integrations = False
intents.invites = False
intents.webhooks = False


activity = discord.Activity(
    type=discord.ActivityType.playing,
    name="Restarting...",
)


bot = haruka.Haruka(
    activity=activity,
    command_prefix=get_prefix,
    intents=intents,
    case_insensitive=True,
    strip_after_prefix=True,
)


@bot.check
async def _blacklist_check(ctx: Context):
    row = await bot.conn.fetchrow(f"SELECT * FROM blacklist WHERE id = '{ctx.author.id}';")
    return row is None


@bot.event
async def on_ready():
    bot.log(f"Logged in as {bot.user}")
    print(f"Logged in as {bot.user}")


@bot.before_invoke
async def _before_invoke(ctx: Context):
    # Count text commands
    if ctx.command.root_parent:
        return

    if await bot.is_owner(ctx.author):
        return

    name = ctx.command.name
    if name not in bot._command_count:
        bot._command_count[name] = []

    bot._command_count[name].append(ctx)

    if ctx.guild:
        await bot.reset_inactivity_counter(ctx.guild.id)
