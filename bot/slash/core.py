from __future__ import annotations

import asyncio
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Type,
    Union,
    TYPE_CHECKING,
)

import asyncpg
import discord
from discord.http import HTTPClient

from .converter import *
from .errors import *
if TYPE_CHECKING:
    import haruka


__all__ = (
    "Command",
    "SlashMixin",
    "parse",
)


PARAMS_MAPPING = {
    1: subcommand_converter,
    6: user_converter,
    7: role_converter,
    8: channel_converter,
}


SlashCallback = Callable[[Interaction], Coroutine[Any, Any, Any]]
MaybeCoroutine = Union[Callable[[Interaction], Any], Callable[[Interaction], Coroutine[Any, Any, Any]]]


class Command:

    __slots__ = (
        "payload",
        "callback",
        "checks",
    )

    if TYPE_CHECKING:
        callback: SlashCallback
        payload: Dict[str, Any]
        checks: List[MaybeCoroutine]

    def __init__(self, callback: SlashCallback, payload: Dict[str, Any]) -> None:
        self.callback = callback
        self.payload = payload
        self.checks = getattr(callback, "__slash_checks__", [])

    def add_check(self, check: MaybeCoroutine) -> None:
        self.checks.append(check)


class SlashMixin:
    """A mixin that provides utilities for slash commands.

    The bot object inherits from this mixin must also subclass
    ``commands.Bot``
    """

    if TYPE_CHECKING:
        _slash_commands: Dict[str, Command]
        _json: List[str, Any]
        http: HTTPClient
        conn: asyncpg.Pool

    def __init_subclass__(cls: Type[haruka.Haruka], **kwargs) -> None:
        cls._slash_commands = {}
        cls._json = []
        super().__init_subclass__(**kwargs)

    def add_slash_command(self, command: Command) -> None:
        """Register a slash command to the internal commands
        mapping.

        It is recommended to use ``slash`` instead.

        Parameters
        -----
        coro: ``SlashCommand``
            The slash command to add
        """
        self._slash_commands[command.payload["name"]] = command
        self._json.append(command.payload)

    def slash(self, payload: Dict[str, Any]) -> Callable[[SlashCallback], Command]:
        """A shortcut decorator that convert a function into ``SlashCommand`` and adds it
        to the internal command list via ``add_slash_command()``.

        Parameters
        -----
        payload: Dict[``str``, Any]
            The slash command payload to register with the Discord API.

        Returns
        -----
        Callable[[``Interaction``], Coroutine[Any, Any, Any]]
            A decorator that converts the provided method into a ``SlashCommand``, adds it
            to the bot, then returns it.
        """
        def decorator(coro: SlashCallback) -> Command:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError(f"Slash command callback must be coroutine, not {coro.__class__.__name__}")

            command = Command(coro, payload)
            self.add_slash_command(command)
            return command
        return decorator

    async def overwrite_slash_commands(self) -> None:
        """This function is a coroutine

        Perform an API call to bulk update all registered slash commands.
        """
        # Wait until ready so that the "user" attribute is available
        await self.wait_until_ready()

        # Now register all slash commands
        self.log(f"Overwriting {len(self._json)} slash commands: " + ", ".join(json["name"] for json in self._json))
        data = await self.http.bulk_upsert_global_commands(self.user.id, self._json)
        self.log(f"Returned JSON:\n{data}")

    async def process_slash_commands(self, interaction: Interaction) -> None:
        """This function is a coroutine

        Process a slash command from an interaction

        Parameters
        -----
        interaction: ``Interaction``
            The interaction to process
        """
        name = interaction.data["name"]
        command = self._slash_commands[name]

        if not interaction.user == self.owner:
            if name not in self._slash_command_count:
                self._slash_command_count[name] = []

            self._slash_command_count[name].append(interaction)

        if interaction.guild_id:
            await self.reset_inactivity_counter(interaction.guild_id)

        try:
            for check in command.checks:
                await discord.utils.maybe_coroutine(check, interaction)
        except Exception as exc:
            self.dispatch("slash_command_error", interaction, exc)
        else:
            try:
                await command.callback(interaction)
            except Exception as exc:
                wrapped = CommandInvokeError(name, exc)
                self.dispatch("slash_command_error", interaction, wrapped)


def parse(interaction: Interaction) -> Dict[str, Any]:
    """Get all slash commands arguments from an interaction

    Parameters
    -----
    interaction: ``Interaction``
        The slash command interaction

    Returns
    -----
    Dict[``str``, Any]
        A mapping of argument objects by their names
    """
    ret = {}

    try:
        options = interaction.data["options"]
    except KeyError:
        return ret

    for option in options:
        key = option["name"]
        converter = PARAMS_MAPPING.get(option["type"])

        if converter is not None:
            value = converter(interaction, **option)
        else:
            value = option["value"]

        ret[key] = value

    return ret
