from __future__ import annotations

import asyncio
import dataclasses
import datetime
import functools
import json
import math
import random
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, Callable, Dict, Generic, List, Literal, Optional, Type, TypeVar, Union, overload

import asyncpg
import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import emoji_ui
import utils
from .abc import Battleable, ClassObject
from .combat import handler
from .core import CT, LT, WT, MISSING


__all__ = (
    "rpg_check",
    "BasePlayer",
    "BaseItem",
    "PlayerCache",
)


T = TypeVar("T")
PT = TypeVar("PT", bound="BasePlayer")
IT = TypeVar("IT", bound="BaseItem")
EXP_SCALE: int = 4


# These keys are inside player.state
BATTLE_KEY: Literal["battle"] = "battle"
TRAVEL_KEY: Literal["travel"] = "travel"
TRAVEL_DESTINATION_KEY: Literal["travel_destination"] = "travel_destination"
TRAVEL_CHANNEL_KEY: Literal["travel_channel_id"] = "travel_channel_id"


class Event(asyncio.Event):
    async def wait_for(self, predicate: Callable[..., bool], *args, **kwargs) -> None:
        while not predicate(*args, **kwargs):
            await asyncio.sleep(0)
            self.clear()
            await self.wait()


class PlayerCache(dict):

    event: Event = Event()

    def __delitem__(self, id: int) -> None:
        self[id] = None
        self.event.set()

    def __setitem__(self, k: int, v: Optional[Ellipsis]) -> None:
        super().__setitem__(k, v)
        self.event.set()


class BattleContext(AbstractAsyncContextManager):

    __slots__ = (
        "player",
    )

    def __init__(self, player: PT) -> None:
        self.player: PT = player

    async def __aenter__(self) -> None:
        self.player.state[BATTLE_KEY] = True
        await self.player.save(state=self.player.state)

    async def __aexit__(self, exc_type: Type[Exception], exc_value: Exception, traceback: TracebackType) -> None:
        self.player.state[BATTLE_KEY] = False
        await self.player.save(state=self.player.state)


class ItemNotFound(Exception):
    """Exception raise when the item ID cannot be found
    in the player's inventory
    """
    pass


@dataclasses.dataclass(init=True, repr=True, order=False, frozen=False)
class BasePlayer(Battleable, Generic[LT, WT]):
    """Base class for players from different worlds

    Each player is represented with an instance of a subclass of this class and
    they should be cached efficiently.

    Attributes
    -----
    name: ``str``
        The player's name, which is the same as Discord name
    id: ``int``
        The player's ID, which is the same as Discord ID
    description: ``str``
        The player's description
    world: ``BaseWorld``
        The world the player is currently in
    location: ``BaseLocation``
        The location the player is currently in
    level: ``int``
        The player's level
    xp: ``int``
        The player's experience point
    money: ``int``
        The player's money
    items: Dict[``int``, ``int``]
        The player's items
    travel: Optional[``datetime.datetime``]
        The datetime when the player will arrive at the destination if he is
        traveling
    hp: ``int``
        The player's current health point
    state: Dict[``str``, Any]
        The player status
    """

    user: discord.User
    description: str
    world: Type[WT]
    location: Type[LT]
    level: int
    xp: int
    money: int
    items: Dict[int, int]
    hp: int
    travel: Optional[datetime.datetime]
    state: Dict[str, Any]

    # Short-hand properties

    @property
    def name(self) -> str:
        return self.user.name

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def client_user(self) -> discord.ClientUser:
        """The bot user acquired from the internal
        ``discord.state.ConnectionState``
        """
        return self.user._state.user

    # Class-specific properties, can be overriden

    @classmethod
    @property
    def display(cls: Type[PT]) -> str:
        return "🧍"

    @classmethod
    @property
    def type_id(cls: Type[PT]) -> int:
        raise NotImplementedError

    # Instance methods

    def traveling(self) -> bool:
        """Whether the player is traveling"""
        return self.state.get(TRAVEL_KEY, False)

    def battling(self) -> bool:
        """Whether the player is battling"""
        return self.state.get(BATTLE_KEY, False)

    def calc_distance(self, destination: Type[LT]) -> float:
        """Calculate the moving distance between the player and
        a location of the same world

        Parameters
        -----
        destination: Type[``BaseLocation``]
            The location to travel to

        Returns
        -----
        ``float``
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
        target: ``discord.TextChannel``
            The target Discord channel to send messages to
        destination: Type[``BaseLocation``]
            The location to travel to
        """
        if not self.world.id == destination.world.id:
            raise ValueError("Destination is in another world")

        if self.level < destination.level_limit:
            return await channel.send(f"You must reach `Lv.{destination.level_limit}` to get access to this location!")

        if self.location.id == destination.id:
            return await channel.send(f"You have been in **{destination.name}** already!")

        if self.battling():
            return await channel.send("Please complete your ongoing battle first!")

        if self.traveling():
            return await channel.send("You have already been on a journey, please get to the destination first!")

        distance: float = self.calc_distance(destination)
        self.travel = discord.utils.utcnow() + datetime.timedelta(seconds=distance)
        self.state[TRAVEL_KEY] = True
        self.state[TRAVEL_DESTINATION_KEY] = destination.id
        self.state[TRAVEL_CHANNEL_KEY] = channel.id
        self = await self.location.on_leaving(self)
        await self.update()
        await channel.send(f"Travelling to **{destination.name}**... You will arrive after {utils.format(distance)}")
        self.user._state.task.travel.restart()

    def prepare_battle(self) -> BattleContext:
        return BattleContext(self)

    async def battle(self, channel: discord.TextChannel) -> PT:
        if self.battling():
            return await channel.send("Please complete your ongoing battle first!")

        if self.traveling():
            return await channel.send("You are currently travelling, cannot initiate battle!")

        if not self.location.creatures:
            return await channel.send("The current location has no enemy to battle")

        async with self.prepare_battle():
            enemy_type: Type[CT] = random.choice(self.location.creatures)
            enemy: CT = enemy_type()
            embed: discord.Embed = enemy.create_embed()
            embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else discord.Embed.Empty)
            message: discord.Message = await channel.send("Do you want to fight this opponent?", embed=embed)

            display: emoji_ui.YesNoSelection = emoji_ui.YesNoSelection(message)
            self.release()
            choice: Optional[bool] = await display.listen(self.id)
            player: PT = await self.from_user(self.user)

            if choice is None:
                return player

            if not choice:
                await channel.send("Retreated")
                return player

            return await handler(channel, player=player, enemy=enemy)

    async def use(self, channel: discord.TextChannel, item_id: int) -> PT:
        """This function is a coroutine
        
        Let this player use an item that only affects himself.

        Parameters
        -----
        channel: ``discord.TextChannel``
            The front-end channel to interact with the user
        item_id: ``int``
            The item ID to use
        
        Returns
        -----
        ``BasePlayer``
            The player after using the item, may remain unchanged
            if a check fails
        """
        try:
            item: Optional[IT] = BaseItem.from_id(item_id)
            if not item:
                raise ItemNotFound
            self = await item.effect(self)
        except ItemNotFound:
            await channel.send(f"I cannot find any items with `ID {item_id}` from your inventory!")
        else:
            await channel.send(f"**{escape(self.user.name)}** consumed 1 **{item.name}**!")
        finally:
            return self

    async def leveled_up_notify(self, target: discord.TextChannel, **kwargs) -> discord.Message:
        return await target.send(f"<@!{self.id}> reached **Lv.{self.level}**.\nHP was fully recovered.", **kwargs)

    async def isekai_notify(self, target: discord.TextChannel, **kwargs) -> discord.Message:
        return await target.send(f"<@!{self.id}> was killed and reincarnated to **{self.world.name}**", **kwargs)

    def gain_xp(self, exp: int) -> bool:
        """Increase the player's experience point and handle
        any calculation logics.

        Parameters
        -----
        exp: ``int``
            The amount of experience points to increase

        Returns
        -----
        ``bool``
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
        ``BasePlayer``
            The player with updated attributes
        """
        from .core import BaseWorld
        from .worlds.earth import EarthWorld

        player: PT = await self.location.on_leaving(self)

        worlds: List[Type[WT]] = BaseWorld.__subclasses__()
        worlds.remove(EarthWorld)  # Imagine isekai back to earth
        player.world = random.choice(worlds)
        player.location = player.world.get_location(0)
        player.state.update(travel=False, battle=False)
        player = await player.location.on_arrival(player)
        player.hp = -1  # A workaround way to set hp = hp_max

        await player.update()
        await player.save(type_id=0)
        player.release()
        return await player.from_user(player.user)

    async def change_class(self, channel: discord.TextChannel) -> PT:
        """This function is a coroutine

        Change the class of this player

        Parameters
        -----
        channel: ``discord.TextChannel``
            The channel to interact with

        Returns
        -----
        ``BasePlayer``
            The player after the operation, this may remain unchanged
            (due to not passing checks, for example)
        """
        if not self.location.class_changable:
            await channel.send("You cannot change your class at this location!")
            return self

        class_display: str = ", ".join(ptype.__name__ for ptype in self.world.ptypes if ptype.type_id > 0)
        embed: discord.Embed = discord.Embed(
            description="Do you want to change your class for `💲1000`?\nYour new class will be chosen *randomly*!\nList of player classes in this world: " + class_display,
            color=0x2ECC71,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name="Class changing",
            icon_url=self.client_user.avatar.url,
        )
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else discord.Embed.Empty)
        message: discord.Message = await channel.send(embed=embed)
        display: emoji_ui.YesNoSelection = emoji_ui.YesNoSelection(message)

        self.release()
        choice: Optional[bool] = await display.listen(self.user.id)
        player = await self.from_user(self.user)
        if choice is None:
            return player

        if choice:
            if player.money < 1000:
                await channel.send("You do not have enough money!")
                return player

            _type: Type[PT] = random.choice(self.world.ptypes)
            while _type.type_id == 0:
                _type = random.choice(self.world.ptypes)
            await player.save(
                money=player.money - 1000,
                type_id=_type.type_id,
                hp=-1,
            )
            await channel.send(f"Your new class is **{_type.__name__}**!")
            player.release()
            return await BasePlayer.from_user(player.user)

    # Embed creation support

    def create_embed(self) -> discord.Embed:
        """Create an embed represents basic information about
        this player

        Returns
        -----
        ``discord.Embed``
            The created embed
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
        _ext: str = ""
        if self.traveling():
            _ext = " (traveling)"
        embed.add_field(
            name="Current location",
            value=f"{self.location.name}{_ext}, {self.world.name}",
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

    def map_inventory(self) -> discord.Embed:
        """Create an embed displaying the player's inventory

        Returns
        -----
        ``discord.Embed``
            The created embed
        """
        _display: List[str] = []
        item: IT
        item_id: int
        item_amount: int
        for item_id, item_amount in self.items.items():
            item = BaseItem.from_id(item_id)
            _display.append(f"`ID {item_id}` **{escape(item.name)}**: {item_amount}")

        embed: discord.Embed = discord.Embed(
            description="\n".join(_display) or "Whoops! Looks like there is nothing here at the moment. You can get items from the lottery and shops!",
            color=0x2ECC71,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=f"{self.user} Inventory",
            icon_url=self.client_user.avatar.url,
        )
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else discord.Embed.Empty)
        return embed

    def map_world(self) -> discord.Embed:
        """Create an embed represents basic information about
        the player's world.

        Returns
        -----
        ``discord.Embed``
            The created embed
        """
        embed: discord.Embed = discord.Embed(
            title=self.world.name,
            description=self.world.description,
            color=0x2ECC71,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="World ID",
            value=f"`ID {self.world.id}`",
        )
        embed.add_field(
            name="Locations",
            value="\n".join(f"`ID {location.id}` {location.name}" for location in self.world.locations),
        )
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else discord.Embed.Empty)
        embed.set_author(
            name="You are currently in",
            icon_url=self.client_user.avatar.url,
        )
        return embed

    def map_location(self, location: Type[LT]) -> discord.Embed:
        """Create an embed represents basic information about
        a location.

        Parameters
        -----
        location: Type[``BaseLocation``]
            The location to create an embed for

        Returns
        -----
        ``discord.Embed``
            The created embed
        """
        embed: discord.Embed = location.create_embed()
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else discord.Embed.Empty)
        embed.set_author(
            name="Location information",
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

    def release(self) -> None:
        """Release control of this player instance,
        it should not be called afterwards.
        """
        cache: PlayerCache = self.user._state.players
        cache[self.id] = None

    def __del__(self) -> None:
        self.release()

    async def update(self) -> None:
        """This function is a coroutine

        Save the instance attributes to the database.
        """
        await self.save(
            description=self.description,
            world=self.world,
            location=self.location,
            type_id=self.type_id,
            level=self.level,
            xp=self.xp,
            money=self.money,
            items=self.items,
            hp=self.hp,
            travel=self.travel,
            state=self.state,
        )

    async def save(self, *, description: str = MISSING, world: Type[WT] = MISSING, location: Type[LT] = MISSING, type_id: int = MISSING,
        level: int = MISSING, xp: int = MISSING, money: int = MISSING, items: Dict[int, int] = MISSING, hp: int = MISSING,
        travel: Optional[datetime.datetime] = MISSING, state: Dict[str, Any] = MISSING,
    ) -> None:
        """This function is a coroutine

        Save this player's data to the database.

        Parameters
        -----
        **kwargs:
            The attributes to save
        """
        counter: int = 0
        updates: List[str] = []
        args: List[Any] = []
        conn: Union[asyncpg.Connection, asyncpg.Pool] = self.user._state.conn

        if description is not MISSING:
            counter += 1
            updates.append(f"description = ${counter}")
            args.append(description)

        if world is not MISSING:
            counter += 1
            updates.append(f"world = ${counter}")
            args.append(world.id)

        if location is not MISSING:
            counter += 1
            updates.append(f"location = ${counter}")
            args.append(location.id)

        if type_id is not MISSING:
            counter += 1
            updates.append(f"type = ${counter}")
            args.append(type_id)

        if level is not MISSING:
            counter += 1
            updates.append(f"level = ${counter}")
            args.append(level)

        if xp is not MISSING:
            counter += 1
            updates.append(f"xp = ${counter}")
            args.append(xp)

        if money is not MISSING:
            counter += 1
            updates.append(f"money = ${counter}")
            args.append(money)

        if items is not MISSING:
            counter += 1
            updates.append(f"items = ${counter}")
            args.append(json.dumps(items))

        if hp is not MISSING:
            counter += 1
            updates.append(f"hp = ${counter}")
            args.append(hp)

        if travel is not MISSING:
            counter += 1
            updates.append(f"travel = ${counter}")
            args.append(travel)

        if state is not MISSING:
            counter += 1
            updates.append(f"state = ${counter}")
            args.append(json.dumps(state))

        if counter == 0:
            return

        content: str = ", ".join(updates)
        query: str = f"UPDATE rpg SET {content} WHERE id = '{self.id}';"
        await conn.execute(query, *args)

    async def delete(self) -> None:
        conn: Union[asyncpg.Connection, asyncpg.Pool] = self.user._state.conn
        await conn.execute(f"DELETE FROM rpg WHERE id = '{self.id}';")

    @classmethod
    async def from_user(cls: Type[PT], user: discord.User) -> Optional[PT]:
        """This function is a coroutine

        Get a player object from a Discord user.

        Parameters
        -----
        user: ``discord.User``
            The Discord user

        Returns
        -----
        Optional[``BasePlayer``]
            The retrieved player, or ``None`` if not found
        """
        from .core import BaseWorld

        cache: PlayerCache = user._state.players
        await cache.event.wait_for(lambda: cache.get(user.id) is None)
        cache[user.id] = ...  # Must be a non-None object (act as a placeholder)

        conn: Union[asyncpg.Connection, asyncpg.Pool] = user._state.conn
        row: asyncpg.Record = await conn.fetchrow(f"SELECT * FROM rpg WHERE id = '{user.id}';")
        if not row:
            cache[user.id] = None
            return

        world: Type[WT] = BaseWorld.from_id(row["world"])
        location: Type[LT] = world.get_location(row["location"])
        ptype: Type[PT] = world.get_player(row["type"])

        items: Dict[int, int] = {}
        for k, v in json.loads(row["items"]).items():
            items[int(k)] = v

        player: PT = ptype(
            user=user,
            description=row["description"],
            world=world,
            location=location,
            level=row["level"],
            xp=row["xp"],
            money=row["money"],
            items=items,
            hp=row["hp"],
            travel=row["travel"],
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
        user: ``discord.User``
            The Discord user

        Returns
        -----
        ``BasePlayer``
            The newly created player

        Exceptions
        -----
        ``ValueError``
            The player has already existed
        """
        conn: Union[asyncpg.Connection, asyncpg.Pool] = user._state.conn
        if await conn.fetchrow(f"SELECT * FROM rpg WHERE id = '{user.id}';"):
            raise ValueError("A player with the same ID exists")

        await conn.execute(
            f"INSERT INTO rpg \
            VALUES ('{user.id}', $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11);",
            "A new player",  # description
            0,  # world
            1,  # location
            0,  # type
            1,  # level
            0,  # exp
            50,  # money
            json.dumps({}),  # items
            -1,  # hp
            None,  # travel
            json.dumps(dict(travel=False, battle=False)),  # state
        )
        return await cls.from_user(user)


class BaseItem(ClassObject, Generic[PT]):
    """Base class for player items.

    All items must subclass this class. Please note that
    item objects are represented by the classes themselves,
    not their instances.

    Attributes
    -----
    name: ``str``
        The item's name
    description: ``str``
        The item's description
    id: ``int``
        The item's ID
    """

    name: str
    description: str
    id: int

    @classmethod
    @overload
    async def effect(cls: Type[IT], user: PT, target: Any) -> PT:
        ...

    @classmethod
    @overload
    async def effect(cls: Type[IT], user: PT) -> PT:
        ...

    @classmethod
    async def effect(cls, user, target=None):
        """This function is a coroutine

        Perform calculation for the effect when a user consumes this item.

        Subclasses must implement this.

        Parameters
        -----
        user: ``BasePlayer``
            The player who consumed this item
        Optional[``Battleable``]
            The effect target, if this item aims at another entity

        Returns
        -----
        ``BasePlayer``
            The player after using the item
        """
        if cls.id not in user.items:
            raise ItemNotFound
        elif user.items[cls.id] <= 0:
            raise ItemNotFound
        else:
            user.items[cls.id] -= 1
            await user.save(items=user.items)
            return user

    @classmethod
    @functools.cache
    def from_id(cls: Type[BaseItem], id: int) -> Optional[Type[IT]]:
        """Construct an item from an ID

        Parameters
        -----
        id: ``int``
            The item ID

        Returns
        -----
        Optional[Type[``BaseItem``]]
            The item with the given ID, or ``None`` if not found
        """
        for itype in utils.get_all_subclasses(cls):
            if getattr(itype, "id", MISSING) == id:
                return itype


def rpg_check() -> Callable[[T], T]:
    async def predicate(ctx: commands.Context) -> bool:
        player: Optional[PT] = await BasePlayer.from_user(ctx.author)
        if player:
            return True

        await ctx.send(f"In order to use RPG commands, you have to invoke `{ctx.prefix}daily` first!")
        return False
    return commands.check(predicate)
