from __future__ import annotations

import asyncio
import contextlib
import datetime
import re
import time
from types import TracebackType
from typing import Any, AsyncIterator, Coroutine, Generic, Iterator, List, Optional, Type, TypeVar, TYPE_CHECKING

import discord
from discord.utils import MISSING


T = TypeVar("T")


def get_all_subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    """A generator that yields all subclasses of a class"""
    for subclass in cls.__subclasses__():
        yield subclass
        yield from get_all_subclasses(subclass)


def slice_string(string: str, offset: int) -> str:
    if len(string) < offset:
        return string

    return string[:offset] + " [...]"


def format(time: float) -> str:
    """Format a given time based on its value.

    Parameters
    -----
    time: ``float``
        The given time, in seconds.

    Returns
    -----
    ``str``
        The formated time (e.g. ``1.50 s``)
    """
    time = float(time)

    if time < 0:
        raise ValueError("time must be a positive value")

    elif time < 1:
        return "{:.2f} ms".format(1000 * time)

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
            if time.is_integer():
                ret.append(f"{int(time)}s")
            else:
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
    args = ["python", "bot/lib/fuzzy.py"]
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


EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def from_unix_format(seconds: int) -> datetime.datetime:
    return EPOCH + datetime.timedelta(seconds=seconds)


class AsyncSequence(Generic[T]):
    """A lazy sequence of coroutines that returns a result of
    a coroutine only when needed.

    All completed coroutines have their results cached within
    the instance. As a result, each coroutine in an instance
    is run at most once.
    """

    __slots__ = ("coros", "_results")
    if TYPE_CHECKING:
        coros: List[Coroutine[Any, Any, T]]
        _results: List[T]

    def __init__(self, coros: List[Coroutine[Any, Any, T]]) -> None:
        self.coros = coros
        self._results = [MISSING] * len(self.coros)

    def __bool__(self) -> bool:
        return len(self.coros) > 0

    def __len__(self) -> int:
        return len(self.coros)

    async def __aiter__(self) -> AsyncIterator[T]:
        for index in range(len(self)):
            yield await self.get(index)

    async def get(self, index: int) -> T:
        """This function is a coroutine

        Runs a coroutine at the specified index and returns its
        result. If this coroutine has been run before then the
        result from the cache will be used instead.
        """
        if self._results[index] is not MISSING:
            return self._results[index]

        self._results[index] = await self.coros[index]
        return self._results[index]
