from __future__ import annotations

import asyncio
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)

import discord
from discord.ext import commands
from discord import http

from .converter import (
    ChannelConverter,
    RoleConverter,
    UserConverter,
)
from .types import (
    CommandOptionPayload,
)


__all__ = (
    "Command",
    "SlashMixin",
    "parse",
)


PARAMS_MAPPING: Dict[int, Callable[[discord.Interaction, str], Any]] = {
    6: UserConverter,
    7: ChannelConverter,
    8: RoleConverter,
}


SlashCallback = Callable[[discord.Interaction], Coroutine[Any, Any, Any]]
MaybeCoroutine = Union[Callable[[discord.Interaction], Any], Callable[[discord.Interaction], Coroutine[Any, Any, Any]]]


class Command:

    __slots__ = (
        "payload",
        "callback",
        "checks",
    )

    def __init__(self, callback: SlashCallback, payload: Dict[str, Any]) -> None:
        self.callback: SlashCallback = callback
        self.payload: Dict[str, Any] = payload
        self.checks: List[MaybeCoroutine] = getattr(callback, "__slash_checks__", [])

    def add_check(self, check: MaybeCoroutine) -> None:
        self.checks.append(check)


class _Proto(Protocol):
    @property
    def http(self) -> http.HTTPClient: ...
    def log(self, content: Any) -> None: ...
    def dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None: ...


class SlashMixin:
    """A mixin that provides utilities for slash commands.

    The bot object inherits from this mixin must also subclass
    :class:`commands.Bot`
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._slash_commands: Dict[str, Command] = {}
        self._json: List[Dict[str, Any]] = []
        super().__init__(*args, **kwargs)

    def add_slash_command(self, command: Command) -> None:
        """Register a slash command to the internal commands
        mapping.

        It is recommended to use :meth:`slash` instead.

        Parameters
        -----
        coro: :class:`SlashCommand`
            The slash command to add
        """
        self._slash_commands[command.payload["name"]] = command
        self._json.append(command.payload)

    def slash(self, payload: Dict[str, Any]) -> Callable[[SlashCallback], Command]:
        """A shortcut decorator that convert a function into :class:`SlashCommand` and adds it
        to the internal command list via :meth:`add_slash_command()`.

        Parameters
        -----
        payload: Dict[:class:`str`, Any]
            The slash command payload to register with the Discord API.

        Returns
        -----
        Callable[[:class:`discord.Interaction`], Coroutine[Any, Any, Any]]
            A decorator that converts the provided method into a :class:`SlashCommand`, adds it
            to the bot, then returns it.
        """
        def decorator(coro: SlashCallback) -> Command:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError(f"Slash command callback must be coroutine, not {coro.__class__.__name__}")

            command: Command = Command(coro, payload)
            self.add_slash_command(command)
            return command
        return decorator

    async def overwrite_slash_commands(self: _Proto) -> None:
        """This function is a coroutine

        Perform an API call to bulk update all registered slash commands.
        """
        # Wait until ready so that the "user" attribute is available
        await self.wait_until_ready()

        # Now register all slash commands
        self.log("Overwriting slash commands: " + ", ".join(json["name"] for json in self._json))
        data: List[Dict[str, Any]] = await self.http.bulk_upsert_global_commands(self.user.id, self._json)
        self.log(f"Returned JSON:\n{data}")

    async def process_slash_commands(self: _Proto, interaction: discord.Interaction) -> None:
        """This function is a coroutine

        Process a slash command from an interaction

        Parameters
        -----
        interaction: :class:`discord.Interaction`
            The interaction to process
        """
        name: str = interaction.data["name"]
        command: Command = self._slash_commands[name]

        try:
            for check in command.checks:
                await discord.utils.maybe_coroutine(check, interaction)

            await command.callback(interaction)
        except Exception as exc:
            self.dispatch("slash_command_error", interaction, exc)


def parse(interaction: discord.Interaction) -> Dict[str, Any]:
    """Get all slash commands arguments from an interaction

    Parameters
    -----
    interaction: :class:`discord.Interaction`
        The slash command interaction

    Returns
    -----
    Dict[:class:`str`, Any]
        A mapping of argument objects by their names
    """
    ret: Dict[str, Any] = {}

    try:
        options: List[CommandOptionPayload] = interaction.data["options"]
    except KeyError:
        return ret

    for option in options:
        key: str = option["name"]
        converter: Optional[Callable[[discord.Interaction, str], Any]] = PARAMS_MAPPING.get(option["type"])

        value: Any
        if converter:
            value = converter(interaction, option["value"])
        else:
            value = option["value"]

        ret[key] = value

    return ret
