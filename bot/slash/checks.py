from typing import Any, Callable, TypeVar

import discord

from .core import (
    Command,
    MaybeCoroutine,
    SlashCallback,
)
from .errors import (
    NoPrivateMessage,
)


__all__ = (
    "check",
    "guild_only",
)


ST = TypeVar("ST", Command, SlashCallback)


def check(predicate: MaybeCoroutine) -> Callable[[ST], ST]:
    def decorator(func: ST) -> ST:
        if isinstance(func, Command):
            func.add_check(predicate)

        elif callable(func):
            if not hasattr(func, "__slash_checks__"):
                func.__slash_checks__ = []
            func.__slash_checks__.append(predicate)

        else:
            raise TypeError(f"Unrecognized type for checking: {func.__class__.__name__}")

        return func

    return decorator


def guild_only() -> Callable[[discord.Interaction], Callable[[ST], ST]]:
    def predicate(interaction: discord.Interaction) -> Any:
        if not interaction.guild_id:
            raise NoPrivateMessage

    return check(predicate)
