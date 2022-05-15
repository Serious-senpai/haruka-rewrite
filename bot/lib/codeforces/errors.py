from __future__ import annotations

from typing import TYPE_CHECKING


__all__ = (
    "CodeforcesException",
)


class CodeforcesException(Exception):

    __slots__ = ("comment",)
    if TYPE_CHECKING:
        comment: str

    def __init__(self, comment: str) -> None:
        self.comment = comment
        super().__init__(comment)
