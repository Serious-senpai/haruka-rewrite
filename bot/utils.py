import contextlib
import time
from types import TracebackType
from typing import Callable, Iterator, List, Optional, Tuple, Type, TypeVar

import discord
from discord.ext import commands


T = TypeVar("T")
TESTING_GUILD_IDS: Tuple[int, ...] = (764494394430193734, 886311355211190372)


def testing() -> Callable[[T], T]:
    """A check indicates that a command is still in the development phase"""
    async def predicate(ctx: commands.Context) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.guild and ctx.guild.id in TESTING_GUILD_IDS:
            return True
        return False
    return commands.check(predicate)


def get_all_subclasses(cls: Type) -> Iterator[Type]:
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
        ret: List[str] = []

        days: int = int(time / 86400)
        time -= days * 86400
        hours: int = int(time / 3600)
        time -= hours * 3600
        minutes: int = int(time / 60)
        time -= minutes * 60

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

    def __init__(self) -> None:
        self._start: float = time.perf_counter()
        self._result: Optional[float] = None

    def __exit__(self, exc_type: Type[Exception], exc_value: Exception, traceback: TracebackType) -> None:
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
