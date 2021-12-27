from typing import TypeVar

import discord


__all__ = (
    "SlashException",
    "CheckFailure",
    "NoPrivateMessage",
    "CommandInvokeError",
)


ET = TypeVar("ET", bound=BaseException)


class SlashException(discord.DiscordException):
    pass


class CheckFailure(SlashException):
    pass


class NoPrivateMessage(CheckFailure):
    def __init__(self, command: str) -> None:
        super().__init__(f"Command '{command}' can only be used in a server text channel.")


class CommandInvokeError(SlashException):
    def __init__(self, command: str, original: ET) -> None:
        self.original: ET = original
        super().__init__(f"Command '{command}' raised an exception: {original.__class__.__name__}: {original}")
