from __future__ import annotations

from collections import namedtuple
from typing import Generic, List, Optional, Tuple, Type, TypeVar, TYPE_CHECKING

from .abc import Battleable

if TYPE_CHECKING:
    from .player import PT


Coordination: Tuple = namedtuple("Coordination", ("x", "y"))
WT = TypeVar("WT", bound="BaseWorld")
LT = TypeVar("LT", bound="BaseLocation")


class BaseWorld(Generic[LT]):
    """Base class for creating new worlds"""

    name: str
    description: str
    id: int
    locations: List[Type[LT]]
    ptypes: List[Type[PT]]

    @classmethod
    def from_id(cls: Type[WT], id: int) -> Optional[Type[WT]]:
        for world in cls.__subclasses__:
            if world.id == id:
                return world

    @classmethod
    def get_location(cls: Type[WT], id: int) -> Optional[Type[LT]]:
        try:
            return cls.locations[id]
        except IndexError:
            return


class BaseLocation(Generic[WT]):
    """Base class for world locations"""

    name: str
    description: str
    id: int
    world: Type[WT]
    coordination: Coordination

    @classmethod
    def from_id(cls: Type[LT], world: Type[WT], id: int) -> Optional[Type[LT]]:
        return world.get_location(id)


class BaseCreature(Battleable, Generic[LT]):
    """Base class for creatures appearing in worlds"""

    name: str
    description: str
    location: Type[LT]
