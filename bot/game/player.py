from __future__ import annotations

import dataclasses
from typing import Any, Generic, List, Optional, Type, TypeVar, Union

import asyncpg
import discord

from .abc import Battleable
from .core import LT, WT, BaseWorld


PT = TypeVar("PT", bound="BasePlayer")
IT = TypeVar("IT", bound="BaseItem")


@dataclasses.dataclass(init=True, repr=True, order=False, frozen=False)
class BasePlayer(Battleable, Generic[LT, WT]):
    """Base class for players from different worlds"""

    __slots__ = (
        "name",
        "id",
        "description",
        "world",
        "location",
        "level",
        "xp",
        "money",
        "items",
        "hp",
    )

    name: str
    id: int
    description: str
    world: Type[WT]
    location: Type[LT]
    level: int
    xp: int
    money: int
    items: List[IT]
    hp: int

    # Possible attributes, should be determined from level

    @property
    def hp_max(self) -> int:
        raise NotImplementedError

    @property
    def physical_atk(self) -> int:
        raise NotImplementedError

    @property
    def magical_atk(self) -> int:
        raise NotImplementedError

    @property
    def physical_res(self) -> int:
        raise NotImplementedError

    @property
    def magical_res(self) -> int:
        raise NotImplementedError

    # Logical operations

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    # Save and load operations

    async def update(self, conn: Union[asyncpg.Connection, asyncpg.Pool]) -> None:
        await conn.execute(f"""
            UPDATE rpg
            SET description = $1, world = $2, location = $3,
                type = $4, level = $5, xp = $6, money = $7,
                items = $8, hp = $9
            WHERE id = '{self.id}';
            """,
            self.description,
            self.world.id,
            self.world.locations.index(self.location.__class__),
            self.world.ptypes.index(self.__class__),
            self.level,
            self.xp,
            self.money,
            [item.id for item in self.items],
            self.hp,
        )

    @classmethod
    async def from_user(
        cls: Type[PT],
        conn: Union[asyncpg.Connection, asyncpg.Pool],
        user: discord.User,
    ) -> Optional[PT]:
        row: asyncpg.Record = await conn.fetchrow(f"SELECT * FROM rpg WHERE id = '{user.id}';")
        if not row:
            return

        world: Type[WT] = BaseWorld.from_id(row["world"])
        location: Type[LT] = world.get_location[row["location"]]
        ptype: Type[PT] = world.ptypes[row["type"]]

        return ptype(
            name=user.name,
            id=user.id,
            description=row["description"],
            world=world,
            location=location,
            level=row["level"],
            xp=row["xp"],
            money=row["money"],
            items=[BaseItem.from_id(item_id) for item_id in row["items"]],
            hp=row["hp"],
        )


class BaseItem(Generic[PT]):
    """Base class for player items"""
    __slots__ = (
        "level",
    )
    name: str
    description: str
    id: int

    def __init__(self, level: int) -> None:
        self.level: int = level

    def effect(self, user: PT, target: Optional[Battleable]) -> Any:
        raise NotImplementedError

    @classmethod
    def from_id(cls: Type[IT], id: str) -> Optional[IT]:
        itype_id, ilevel = [int(s) for s in id.split(".")]
        for itype in cls.__subclasses__:
            if itype.id == itype_id:
                return itype(ilevel)
