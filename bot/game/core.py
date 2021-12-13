from __future__ import annotations

import functools
from collections import namedtuple
from typing import Generic, List, Optional, Tuple, Type, TypeVar, TYPE_CHECKING

from .abc import Battleable

if TYPE_CHECKING:
    from .player import PT


Coordination: Tuple = namedtuple("Coordination", ("x", "y"))
WT = TypeVar("WT", bound="BaseWorld")
LT = TypeVar("LT", bound="BaseLocation")


class BaseWorld(Generic[LT]):
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
    locations: List[:class:`BaseLocation`]
        The locations that this world has
    ptypes: List[:class:`BasePlayer`]
        List of occupations that a player can have in this world
    """

    name: str
    description: str
    id: int
    locations: List[Type[LT]]
    ptypes: List[Type[PT]]

    @classmethod
    @functools.cache
    def from_id(cls: Type[WT], id: int) -> Optional[Type[WT]]:
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
        for world in cls.__subclasses__:
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


class BaseLocation(Generic[WT]):
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
    coordination: :class:`Coordination`
        The coordination of this location in its world
    """

    name: str
    description: str
    id: int
    world: Type[WT]
    coordination: Coordination

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


class BaseCreature(Battleable, Generic[LT]):
    """Base class for creatures appearing in worlds

    Attributes
    -----
    name: :class:`str`
        The creature's name
    description: :class:`str`
        The creature's description
    location: :class:`BaseLocation`
        The location where this creature can be found
    """

    name: str
    description: str
    location: Type[LT]
