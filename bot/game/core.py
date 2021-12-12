from __future__ import annotations

from collections import namedtuple
from typing import Generic, List, Tuple, Type, TypeVar, TYPE_CHECKING

from .abc import Battleable

if TYPE_CHECKING:
    from .player import PT


Coordination: Tuple = namedtuple("Coordination", ("x", "y"))
WT = TypeVar("WT", bound="BaseWorld")
LT = TypeVar("LT", bound="BaseLocation")


class BaseWorld(Generic[LT]):
    """Base class for creating new worlds"""

    def __init__(
        self,
        name: str,
        description: str,
        *,
        id: int,
        locations: List[LT],
        ptypes: List[Type[PT]],
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.id: int = id
        self.locations: List[LT] = locations
        self.ptypes: List[Type[PT]] = ptypes


class BaseLocation(Generic[WT]):
    """Base class for world locations"""

    def __init__(
        self,
        name: str,
        description: str,
        *,
        world: WT,
        coordination: Coordination,
    ) -> None:
        self.name = name
        self.description = description
        self.world: WT = world
        self.coordination: Coordination = coordination


class BaseCreature(Battleable, Generic[LT]):
    """Base class for creatures appearing in worlds"""

    def __init__(
        self,
        name: str,
        description: str,
        *,
        location: LT,
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.location: LT = location
