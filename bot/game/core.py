from __future__ import annotations

import functools
from collections import namedtuple
from typing import (
    Any,
    Generic,
    List,
    NamedTuple,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

import discord

from .abc import Battleable

if TYPE_CHECKING:
    from .player import PT


__all__ = (
    "Coordination",
    "BaseWorld",
    "BaseLocation",
    "BaseEvent",
    "BaseCreature",
)


MISSING: Any = discord.utils.MISSING
WT = TypeVar("WT", bound="BaseWorld")
LT = TypeVar("LT", bound="BaseLocation")
ET = TypeVar("ET", bound="BaseEvent")
CT = TypeVar("CT", bound="BaseCreature")


class ClassObject:
    def __init__(self, *args, **kwargs) -> None:
        raise TypeError("This object is represented by the class itself")


class Coordination(NamedTuple):
    """The coordination of a location"""
    x: int
    y: int


class BaseWorld(ClassObject, Generic[LT, PT, ET]):
    """Base class for creating new worlds.

    All worlds must inherit from this class. Please note that
    world objects are represented by the classes themselves,
    not by their instances.

    Attributes
    -----
    name: :class:`str`
        The world's name
    description: :class:`str`
        The world's description
    id: :class:`int`
        The world's ID
    """

    name: str
    description: str
    id: int
    location: Type[LT]
    ptype: Type[PT]
    event: Type[ET]

    @classmethod
    @property
    def locations(cls: Type[WT]) -> List[Type[LT]]:
        """List of locations in this world"""
        return cls.location.__subclasses__()

    @classmethod
    @property
    def ptypes(cls: Type[WT]) -> List[Type[PT]]:
        """List of types that a player can have in this world"""
        return cls.ptype.__subclasses__()

    @classmethod
    @property
    def events(cls: Type[WT]) -> List[Type[ET]]:
        """List of events that can happened in this world"""
        return cls.event.__subclasses__()

    @classmethod
    @functools.cache
    def from_id(cls: Type[BaseWorld], id: int) -> Optional[Type[WT]]:
        """Get a world from its ID

        Parameters
        -----
        id: :class:`int`
            The world ID

        Returns
        -----
        Optional[Type[:class:`BaseWorld`]]
            The world with the given ID, or ``None`` if not found
        """
        for world in cls.__subclasses__():
            if world.id == id:
                return world

    @classmethod
    def get_location(cls: Type[WT], id: int) -> Optional[Type[LT]]:
        """Get a location that belongs to this world from a given ID

        Parameters
        -----
        id: :class:`int`
            The location ID

        Returns
        -----
        Optional[Type[:class:`BaseLocation`]]
            The location with the given ID, or ``None`` if not found
        """
        try:
            return cls.locations[id]
        except IndexError:
            return


class BaseLocation(ClassObject, Generic[WT, CT]):
    """Base class for world locations

    Please note that location objects are represented by the
    classes themselves, not by their instances.

    Attributes
    -----
    name: :class:`str`
        The location's name
    description: :class:`str`
        The location's description
    id: :class:`int`
        The location's ID
    world: Type[:class:`BaseWorld`]
        The world that this location belongs to
    coordination: :class:`Coordination`
        The coordination of this location in its world
    """

    name: str
    description: str
    id: int
    world: Type[WT]
    coordination: Coordination
    creature: Type[CT]

    @classmethod
    @property
    def creatures(cls: Type[LT]) -> List[Type[CT]]:
        """List of creatures that can be found in this location"""
        return cls.creature.__subclasses__()

    @classmethod
    def from_id(cls: Type[LT], world: Type[WT], id: int) -> Optional[Type[LT]]:
        """Get a location that belongs to a world from a given ID

        Parameters
        -----
        world: :class:`BaseWorld`
            The world to search from
        id: :class:`int`
            The location ID

        Returns
        -----
        Optional[Type[:class:`BaseLocation`]]
            The location with the given ID in the given world, or
            ``None`` if not found
        """
        return world.get_location(id)


class BaseEvent(ClassObject, Generic[WT]):
    """Base class for world events

    Please note that event objects are represented by the
    classes themselves, not by their instances.

    Attributes
    -----
    name: :class:`str`
        The event's name
    description: :class:`str`
        The event's description
    world: Type[:class:`BaseWorld`]
        The world that this event belongs to
    rate: :class:`float`
        The rate at which this event can happen (range 0 - 1)
    """
    name: str
    description: str
    world: Type[WT]
    rate: float

    @classmethod
    async def run(
        cls: Type[ET],
        target: discord.TextChannel,
        player: PT,
    ) -> None:
        """This function is a coroutine

        This is called when the event happens to a player

        Parameters
        -----
        target: :class:`discord.TextChannel`
            The target Discord channel to send messages to
        player: :class:`BasePlayer`
            The player that encounters the event
        """
        raise NotImplementedError


class BaseCreature(Battleable, Generic[LT]):
    """Base class for creatures appearing in worlds

    Attributes
    -----
    name: :class:`str`
        The creature's name
    description: :class:`str`
        The creature's description
    display: :class:`str`
        The emoji to display the player, this does not need
        to be a Unicode emoji
    rate: :class:`float`
        The rate for a player to encounter this creature
        (range 0 - 1)
    """
    name: str
    description: str
    display: str
    rate: float

    def __init__(self) -> None:
        self.hp: int = self.hp_max
