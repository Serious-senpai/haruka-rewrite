from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Type, TypeVar

import asyncpg

from game.abc import Battleable, JSONMetaObject
from game.core import (
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
)
from game.player import PT, BasePlayer


ALT = TypeVar("ALT", bound="_AngpriakeLocation")
AET = TypeVar("AET", bound="_AngpriakeEvent")
ACT = TypeVar("ACT", bound="_AngpriakeCreature")
APT = TypeVar("APT", bound="_AngpriakePlayer")


with open("./bot/game/worlds/angpriake/angpriake.json", "r", encoding="utf-8") as f:
    meta: Dict[str, Dict[str, Any]] = json.load(f)


class _AngpriakeLocation(BaseLocation): ...
class _AngpriakeEvent(BaseEvent): ...
class _AngpriakePlayer(BasePlayer): ...
class _AngpriakeCreature(BaseCreature): ...
class _AngpriakeVillageCreature(_AngpriakeCreature): ...
class _AngpriakeChurchCreature(_AngpriakeCreature): ...
class _AngpriakeCapitalCityCreature(_AngpriakeCreature): ...
class _AngpriakeForestCreature(_AngpriakeCreature): ...


class AngpriakeWorld(BaseWorld, JSONMetaObject, meta=meta):
    location = _AngpriakeLocation
    ptype = _AngpriakePlayer
    event = _AngpriakeEvent


class Village(_AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeVillageCreature

    tasks: Dict[int, asyncio.Task] = {}

    @classmethod
    async def _stonks(cls: Type[Village], conn: asyncpg.Pool, id: int) -> None:
        while await asyncio.sleep(360, True):
            await conn.execute(f"UPDATE rpg SET money = money + 1 WHERE id = '{id}';")

    @classmethod
    async def on_leaving(cls: Type[Village], player: PT) -> PT:
        cls.tasks[player.id].cancel()
        return player

    @classmethod
    async def on_arrival(cls: Type[Village], player: PT) -> PT:
        cls.tasks[player.id] = asyncio.create_task(cls._stonks(player.user._state.conn, player.id))
        return player


class Church(_AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeChurchCreature


class CapitalCity(_AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeCapitalCityCreature

    tasks: Dict[int, asyncio.Task] = {}

    @classmethod
    async def _stonks(cls: Type[Village], conn: asyncpg.Pool, id: int) -> None:
        while await asyncio.sleep(180, True):
            await conn.execute(f"UPDATE rpg SET money = money + 1 WHERE id = '{id}';")

    @classmethod
    async def on_leaving(cls: Type[Village], player: PT) -> PT:
        cls.tasks[player.id].cancel()
        return player

    @classmethod
    async def on_arrival(cls: Type[Village], player: PT) -> PT:
        cls.tasks[player.id] = asyncio.create_task(cls._stonks(player.user._state.conn, player.id))
        return player


class Forest(_AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeForestCreature


class Duck(_AngpriakeForestCreature, JSONMetaObject, meta=meta): ...


class Rabbit(_AngpriakeForestCreature, JSONMetaObject, meta=meta): ...


class Eagle(_AngpriakeForestCreature, JSONMetaObject, meta=meta):
    def attack(self, target: Battleable) -> int:
        return self.physical_attack(target)


class Elephant(_AngpriakeForestCreature, JSONMetaObject, meta=meta):
    def attack(self, target: Battleable) -> int:
        return self.physical_attack(target)


class Thief(_AngpriakeCapitalCityCreature, JSONMetaObject, meta=meta): ...


class Villager(_AngpriakePlayer):
    @classmethod
    @property
    def type_id(cls: Type[Villager]) -> int:
        return 0

    @property
    def hp_max(self) -> int:
        return 110 + self.level

    @property
    def physical_atk(self) -> int:
        return 5 + self.level

    @property
    def magical_atk(self) -> int:
        return self.level

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 20)

    @property
    def magical_res(self) -> float:
        return 0.0

    @property
    def crit_rate(self) -> float:
        return 0.5

    @property
    def crit_dmg(self) -> float:
        return 0.5


class Warrior(_AngpriakePlayer):
    @classmethod
    @property
    def display(cls: Type[Warrior]) -> str:
        return "💂"

    @classmethod
    @property
    def type_id(cls: Type[Warrior]) -> int:
        return 1

    @property
    def hp_max(self) -> int:
        return 200 + 3 * self.level

    @property
    def physical_atk(self) -> int:
        return 10 + 2 * self.level

    @property
    def magical_atk(self) -> int:
        return 0

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 10)

    @property
    def magical_res(self) -> float:
        return self.level / (self.level + 15)

    @property
    def crit_rate(self) -> float:
        return 0.5

    @property
    def crit_dmg(self) -> float:
        return 0.8

    def attack(self, target: Battleable) -> int:
        return self.physical_attack(target)


class Mage(_AngpriakePlayer):
    @classmethod
    @property
    def display(cls: Type[Mage]) -> str:
        return "🧙"

    @classmethod
    @property
    def type_id(cls: Type[Mage]) -> int:
        return 2

    @property
    def hp_max(self) -> int:
        return 150 + 2 * self.level

    @property
    def physical_atk(self) -> int:
        return 0

    @property
    def magical_atk(self) -> int:
        return 15 + 3 * self.level

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 5)

    @property
    def magical_res(self) -> float:
        return self.level / (self.level + 5)

    @property
    def crit_rate(self) -> float:
        return 0.5

    @property
    def crit_dmg(self) -> float:
        return 0.8

    def attack(self, target: Battleable) -> int:
        return self.magical_attack(target)
