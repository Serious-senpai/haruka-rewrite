import contextlib
import time
from types import TracebackType
from typing import List, Optional, Type


def format(time: float) -> str:
    """Format a given time based on its value.

    Parameters
    -----
    time: :class:`float`
        The given time, in seconds.

    Returns
    -----
    :class:`str`
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
