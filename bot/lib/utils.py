from __future__ import annotations

import asyncio
import contextlib
import re
import time
from types import TracebackType
from typing import Callable, Iterator, Optional, Type, TypeVar, TYPE_CHECKING

import discord
from discord.ext import commands

from _types import Context


T = TypeVar("T")
TESTING_GUILD_IDS = (764494394430193734, 886311355211190372)


def testing() -> Callable[[T], T]:
    """A check indicates that a command is still in the development phase"""
    async def predicate(ctx: Context) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.guild and ctx.guild.id in TESTING_GUILD_IDS:
            return True
        return False
    return commands.check(predicate)


def get_all_subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    """A generator that yields all subclasses of a class"""
    for subclass in cls.__subclasses__():
        yield subclass
        yield from get_all_subclasses(subclass)


def format(time: float) -> str:
    """Format a given time based on its value.

    Parameters
    -----
    time: ``float``
        The given time, in seconds.

    Returns
    -----
    ``str``
        The formated time (e.g. ``1.5 s``)
    """
    if time < 1:
        return "{:.2f} ms".format(1000 * time)
    elif time < 60:
        return "{:.2f} s".format(time)
    else:
        days = int(time / 86400)
        time -= days * 86400
        hours = int(time / 3600)
        time -= hours * 3600
        minutes = int(time / 60)
        time -= minutes * 60

        ret = []
        if days > 0:
            ret.append(f"{days}d")
        if hours > 0:
            ret.append(f"{hours}h")
        if minutes > 0:
            ret.append(f"{minutes}m")
        if time > 0:
            ret.append("{:.2f}s".format(time))

        return " ".join(ret)


class TimingContextManager(contextlib.AbstractContextManager):
    """Measure the execution time of a code block."""

    __slots__ = (
        "_start",
        "_result",
    )
    if TYPE_CHECKING:
        _start: float
        _result: Optional[float]

    def __init__(self) -> None:
        self._start = time.perf_counter()
        self._result = None

    def __enter__(self) -> TimingContextManager:
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        self._result = time.perf_counter() - self._start

    @property
    def result(self) -> float:
        """The execution time since the entrance of this
        context manager. Note that this property will
        be unchanged after exiting the code block.
        """
        if self._result is None:
            return time.perf_counter() - self._start

        return self._result


def get_reply(message: discord.Message) -> Optional[discord.Message]:
    """Get the message that ``message`` is replying (to be precise,
    refering) to

    Parameters
    -----
    message: ``discord.Message``
        The target message to fetch information about

    Returns
    -----
    Optional[``discord.Message``]
        The message that this message refers to
    """
    if not message.reference:
        return

    return message.reference.cached_message


async def fuzzy_match(string: str, against: Iterator[str], *, pattern: str = r"\w+") -> str:
    args = ["python", "./bot/levenshtein.py"]
    args.append(string)
    args.extend(against)

    process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
    _stdout, _ = await process.communicate()
    stdout = _stdout.decode("utf-8")
    match = re.search(pattern, stdout)
    if match is not None:
        return match.group()

    raise RuntimeError(f"Cannot match regex pattern {repr(pattern)} with stdout {stdout}")


async def coro_func(value: T) -> T:
    return value
