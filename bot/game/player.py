from __future__ import annotations

import dataclasses
import datetime
import functools
import json
import math
import random
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

import asyncpg
import discord
from discord.ext import commands

import emoji_ui
import utils
from .abc import Battleable, ClassObject
from .combat import handler
from .core import CT, LT, WT


__all__ = (
    "rpg_check",
    "BasePlayer",
    "BaseItem",
)


T = TypeVar("T")
PT = TypeVar("PT", bound="BasePlayer")
IT = TypeVar("IT", bound="BaseItem")
EXP_SCALE: int = 4


@dataclasses.dataclass(init=True, repr=True, order=False, frozen=False)
class BasePlayer(Battleable, Generic[LT, WT]):
    """Base class for players from different worlds

    Each player is represented with an instance of a subclass of this class and
    they should be cached efficiently.

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
    state: Dict[:class:`str`, Any]
        The player status
    """

    user: discord.User
    description: str
    world: Type[WT]
    location: Type[LT]
    level: int
    xp: int
    money: int
    items: List[IT]
    hp: int
    state: Dict[str, Any]

    @property
    def name(self) -> str:
        return self.user.name

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def display(self) -> str:
        return self.state["display"]

    @property
    def client_user(self) -> discord.ClientUser:
        return self.user._state.user

    @classmethod
    @property
    def type_id(cls: Type[PT]) -> int:
        raise NotImplementedError

    def calc_distance(self, destination: Type[LT]) -> float:
        """Calculate the moving distance between the player and
        a location of the same world

        Parameters
        -----
        destination: Type[:class:`BaseLocation`]
            The location to travel to

        Returns
        -----
        :class:`float`
            The distance to travel
        """
        _dx: int = self.location.coordination.x - destination.coordination.x
        _dy: int = self.location.coordination.y - destination.coordination.y
        distance: float = math.sqrt(_dx ** 2 + _dy ** 2)
        return distance

    async def travel_to(
        self,
        channel: discord.TextChannel,
        destination: Type[LT],
    ) -> None:
        """This function is a coroutine

        Travel to the destination location.

        Parameters
        -----
        target: :class:`discord.TextChannel`
            The target Discord channel to send messages to
        destination: Type[:class:`BaseLocation`]
            The location to travel to
        """
        if not self.world.id == destination.world.id:
            raise ValueError("Destination is in another world")

        if self.level < destination.level_limit:
            return await channel.send(f"You must reach `Lv.{destination.level_limit}` to get access to this location!")

        if self.location.id == destination.id:
            return await channel.send(f"You have been in **{destination.name}** already!")

        if self.state.get("travelling", False):
            return await channel.send("You have already been on a journey, please get to the destination first!")

        self.state["travelling"] = True
        await self.update()
        distance: float = self.calc_distance(destination)
        _dest_time: datetime.datetime = discord.utils.utcnow() + datetime.timedelta(seconds=distance)
        notify: discord.Message = await channel.send(f"Travelling to **{destination.name}**... You will arrive after {utils.format(distance)}")
        await discord.utils.sleep_until(_dest_time)
        self.location = destination
        await self.update()

        try:
            await notify.edit(f"<@!{self.id}> arrived at **{destination.name}**")
        except discord.HTTPException:
            pass

        self.state["travelling"] = False
        await self.update()
        for event in self.world.events:
            if event.location.id == self.location.id:
                if random.random() < event.rate:
                    await event.run(channel, self)

    async def battle(self, channel: discord.TextChannel) -> PT:
        if self.state.get("travelling", False):
            return await channel.send("You are currently travelling, cannot initiate battle!")

        if not self.location.creatures:
            return await channel.send("The current location has no enemy to battle")

        enemy_type: Type[CT] = random.choice(self.location.creatures)
        enemy: CT = enemy_type()
        message: discord.Message = await channel.send("Do you want to fight this opponent?", embed=enemy.create_embed())
        display: emoji_ui.YesNoSelection = emoji_ui.YesNoSelection(message)
        choice: Optional[bool] = await display.listen(self.id)

        if choice is None:
            return self

        if not choice:
            await channel.send("Retreated")
            return self

        return await handler(
            channel,
            player=self,
            enemy=enemy,
        )

    async def leveled_up_notify(self, target: discord.TextChannel, **kwargs) -> discord.Message:
        return await target.send(f"<@!{self.id}> reached **Lv.{self.level}**. HP was fully recovered.", **kwargs)

    async def isekai_notify(self, target: discord.TextChannel, **kwargs) -> discord.Message:
        return await target.send(f"<@!{self.id}> was killed and reincarnated to **{self.world.name}**", **kwargs)

    def gain_xp(self, exp: int) -> bool:
        """Increase the player's experience point and handle
        any calculation logics.

        Parameters
        -----
        exp: :class:`int`
            The amount of experience points to increase

        Returns
        -----
        :class:`bool`
            Returns ``True`` if the player leveled up, ``False``
            otherwise
        """
        self.xp += exp
        ret: bool = False

        while self.xp >= EXP_SCALE * self.level:
            self.xp -= EXP_SCALE * self.level
            self.level += 1
            ret = True

        return ret

    async def isekai(self) -> PT:
        """Transfer this player to another world

        Returns
        -----
        :class:`BasePlayer`
            The player with updated attributes
        """
        from .core import BaseWorld
        from .worlds.earth import EarthWorld

        worlds: List[Type[WT]] = BaseWorld.__subclasses__()
        worlds.remove(EarthWorld)  # Imagine isekai back to earth
        world: Type[WT] = random.choice(worlds)
        self.world = world
        self.location = world.get_location(0)
        self.hp = -1  # A workaround way to set hp = hp_max
        await self.update(isekai=True)
        return await self.from_user(self.user)

    def create_embed(self) -> discord.Embed:
        """Create an embed represents basic information about
        this player
        """
        embed: discord.Embed = discord.Embed(
            description=f"Lv.{self.level} (EXP {self.xp}/{EXP_SCALE * self.level})",
            color=0x2ECC71,
            timestamp=discord.utils.utcnow(),
        )

        embed.add_field(
            name="Class",
            value=f"{self.display} {self.__class__.__name__}",
        )
        embed.add_field(
            name="Cash",
            value=f"`💲{self.money}`",
        )
        embed.add_field(
            name="Location",
            value=f"{self.location.name}, {self.world.name} `ID {self.world.id}`",
        )
        embed.add_field(
            name="HP",
            value=f"{self.hp}/{self.hp_max}",
            inline=False,
        )
        embed = super().append_status(embed)
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else discord.Embed.Empty)
        embed.set_author(
            name=f"{self.user} Information",
            icon_url=self.client_user.avatar.url,
        )

        return embed

    def map_world(self) -> discord.Embed:
        """Create an embed represents basic information about
        the player's world
        """
        embed: discord.Embed = discord.Embed(
            title=self.world.name,
            description=self.world.description,
            color=0x2ECC71,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="World ID",
            value=self.world.id,
        )
        embed.add_field(
            name="Locations",
            value="\n".join(f"`ID {location.id}` {location.name}" for location in self.world.locations),
        )
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else discord.Embed.Empty)
        embed.set_author(
            name="World Information",
            icon_url=self.client_user.avatar.url,
        )
        return embed

    # Logical operations

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.id == other.id
        return False

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    # Save and load operations

    async def update(self, *, isekai: bool = False) -> None:
        """This function is a coroutine

        Save this player's data to the database.

        Parameters
        -----
        isekai: :class:`bool`
            Whether to set type_id back to ``0``, default to ``False``
        """
        conn: Union[asyncpg.Connection, asyncpg.Pool] = self.user._state.conn
        await conn.execute(
            f"UPDATE rpg \
            SET description = $1, world = $2, location = $3, \
                type = $4, level = $5, xp = $6, money = $7, \
                items = $8, hp = $9, state = $10 \
            WHERE id = '{self.id}';",
            self.description,
            self.world.id,
            self.location.id,
            0 if isekai else self.type_id,
            self.level,
            self.xp,
            self.money,
            [item.id for item in self.items],
            self.hp,
            json.dumps(self.state),
        )

    async def delete(self) -> None:
        conn: Union[asyncpg.Connection, asyncpg.Pool] = self.user._state.conn
        await conn.execute(f"DELETE FROM rpg WHERE id = '{self.id}';")

    @classmethod
    async def from_user(cls: Type[PT], user: discord.User) -> Optional[PT]:
        """This function is a coroutine

        Get a player object from a Discord user

        Parameters
        -----
        user: :class:`discord.User`
            The Discord user

        Returns
        -----
        Optional[:class:`BasePlayer`]
            The retrieved player, or ``None`` if not found
        """
        from .core import BaseWorld

        conn: Union[asyncpg.Connection, asyncpg.Pool] = user._state.conn
        row: asyncpg.Record = await conn.fetchrow(f"SELECT * FROM rpg WHERE id = '{user.id}';")
        if not row:
            return

        world: Type[WT] = BaseWorld.from_id(row["world"])
        location: Type[LT] = world.get_location(row["location"])
        ptype: Type[PT] = world.get_player(row["type"])

        player: PT = ptype(
            user=user,
            description=row["description"],
            world=world,
            location=location,
            level=row["level"],
            xp=row["xp"],
            money=row["money"],
            items=[BaseItem.from_id(item_id) for item_id in row["items"]],
            hp=row["hp"],
            state=json.loads(row["state"]),
        )
        if player.hp == -1:
            player.hp = player.hp_max
        return player

    @classmethod
    async def make_new(cls: Type[PT], user: discord.User) -> Optional[PT]:
        """This function is a coroutine

        Create a new player from a Discord user

        Parameters
        -----
        user: :class:`discord.User`
            The Discord user

        Returns
        -----
        :class:`BasePlayer`
            The newly created player

        Exceptions
        -----
        :class:`ValueError`
            The player has already existed
        """
        conn: Union[asyncpg.Connection, asyncpg.Pool] = user._state.conn
        if await conn.fetchrow(f"SELECT * FROM rpg WHERE id = '{user.id}';"):
            raise ValueError("A player with the same ID exists")

        await conn.execute(
            f"INSERT INTO rpg \
            VALUES ('{user.id}', $1, $2, $3, $4, $5, $6, $7, $8, $9, $10);",
            "A new player",  # description
            0,  # world
            1,  # location
            0,  # type
            1,  # level
            0,  # exp
            50,  # money
            [],  # items
            -1,  # hp
            json.dumps({"display": "🧍"}),  # state
        )
        return await cls.from_user(user)


class BaseItem(ClassObject, Generic[PT]):
    """Base class for player items.

    All items must subclass this class. Please note that
    item objects are represented by the classes themselves,
    not by their instances.

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

    def effect(self, user: PT, target: Optional[Battleable]) -> Any:
        """Perform calculation for the effect when a user consumes this item.

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
    @functools.cache
    def from_id(cls: Type[BaseItem], id: int) -> Optional[Type[IT]]:
        """Construct an item from an identification string

        Parameters
        -----
        id: :class:`int`
            The item ID

        Returns
        -----
        Optional[Type[:class:`BaseItem`]]
            The item with the given ID, or ``None`` if not found
        """
        for itype in cls.__subclasses__():
            if itype.id == id:
                return itype


def rpg_check() -> Callable[[T], T]:
    async def predicate(ctx: commands.Context) -> bool:
        player: Optional[PT] = await BasePlayer.from_user(ctx.author)
        if player:
            return True

        await ctx.send(f"In order to use RPG commands, you have to invoke `{ctx.prefix}daily` first!")
        return False
    return commands.check(predicate)
