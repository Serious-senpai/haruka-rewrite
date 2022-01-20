from typing import TYPE_CHECKING

import discord


__all__ = (
    "SlashException",
    "CheckFailure",
    "NoPrivateMessage",
    "CommandInvokeError",
)


class SlashException(discord.DiscordException):
    pass


class CheckFailure(SlashException):
    pass


class NoPrivateMessage(CheckFailure):
    def __init__(self, command: str) -> None:
        super().__init__(f"Command '{command}' can only be used in a server text channel.")


class CommandInvokeError(SlashException):

    if TYPE_CHECKING:
        original: Exception

    def __init__(self, command: str, original: Exception) -> None:
        self.original = original
        super().__init__(f"Command '{command}' raised an exception: {original.__class__.__name__}: {original}")
