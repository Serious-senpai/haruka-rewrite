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
    """Base class for players from different worlds

    Each player is represented with an instance of a subclass of this class, and
    it is up to the developer to choose whether to cache the player objects or not.

    Attributes
    -----
    name: :class:`str`
        The player's name, which is the same as Discord name
    id: :class:`int`
        The player's ID, which is the same as Discord ID
    description: :class:`str`
        The player's description
    world: :class:`BaseWorld`
        The world the player is currently in
    location: :class:`BaseLocation`
        The location the player is currently in
    level: :class:`int`
        The player's level
    xp: :class:`int`
        The player's experience point
    money: :class:`int`
        The player's money
    items: List[:class:`BaseItem`]
        The player's items
    hp: :class:`int`
        The player's current health point
    """

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
    type_id: int

    # Logical operations

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    # Save and load operations

    async def update(self, conn: Union[asyncpg.Connection, asyncpg.Pool]) -> None:
        """This function is a coroutine

        Save this player's data to the database.

        Parameters
        -----
        conn: Union[:class:`asyncpg.Connection`, :class:`asyncpg.Pool`]
            The connection or pool to perform the operation
        """
        await conn.execute(
            f"UPDATE rpg \
            SET description = $1, world = $2, location = $3, \
                type = $4, level = $5, xp = $6, money = $7, \
                items = $8, hp = $9 \
            WHERE id = '{self.id}';",
            self.description,
            self.world.id,
            self.location.id,
            self.type_id,
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
        """This function is a coroutine

        Get a player object from a Discord user

        Parameters
        -----
        conn: Union[:class:`asyncpg.Connection`, :class:`asyncpg.Pool`]
            The connection or pool to perform the operation
        user: :class:`discord.User`
            The Discord user

        Returns
        -----
        Optional[:class:`BasePlayer`]
            The retrieved player, or ``None`` if not found
        """
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
            type_id=row["type"],
        )


class BaseItem(Generic[PT]):
    """Base class for player items.

    All items must subclass this class.

    Attributes
    -----
    name: :class:`str`
        The item's name
    description: :class:`str`
        The item's description
    id: :class:`int`
        The item's id
    level: :class:`int`
        The item's level
    """
    __slots__ = (
        "level",
    )
    name: str
    description: str
    id: int

    def __init__(self, level: int) -> None:
        self.level: int = level

    def effect(self, user: PT, target: Optional[Battleable]) -> Any:
        """Perform calculation for the effect when a user consumes this item.
\
        Subclasses must implement this.

        Parameters
        -----
        user: :class:`BasePlayer`
            The player who consumed this item
        Optional[:class:`Battleable`]
            The effect target, if this item aims at another entity
        """
        raise NotImplementedError

    @classmethod
    def from_id(cls: Type[IT], ident: str) -> Optional[IT]:
        """Construct an item from an identification string

        Parameters
        -----
        ident: :class:`str`
            The identification string

        Returns
        -----
        Optional[:class:`BaseItem`]
            The constructed item, or ``None`` is the identification string
            points to an invalid item type ID
        """
        itype_id, ilevel = [int(s) for s in ident.split(".")]
        for itype in cls.__subclasses__:
            if itype.id == itype_id:
                return itype(ilevel)
