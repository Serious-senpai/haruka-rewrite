import discord


__all__ = (
    "SlashException",
    "CheckFailure",
    "NoPrivateMessage",
)


class SlashException(discord.DiscordException):
    pass


class CheckFailure(SlashException):
    pass


class NoPrivateMessage(CheckFailure):
    pass
