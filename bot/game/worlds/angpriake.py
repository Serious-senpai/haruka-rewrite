from __future__ import annotations

import asyncio
from typing import Dict, Type, TypeVar

import asyncpg

from ..abc import Battleable
from ..core import (
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
    Coordination,
)
from ..player import PT, BasePlayer


ALT = TypeVar("ALT", bound="_AngpriakeLocation")
AET = TypeVar("AET", bound="_AngpriakeEvent")
ACT = TypeVar("ACT", bound="_AngpriakeCreature")
APT = TypeVar("APT", bound="_AngpriakePlayer")


class _AngpriakeLocation(BaseLocation):
    ...


class _AngpriakeEvent(BaseEvent):
    ...


class _AngpriakePlayer(BasePlayer):
    ...


class _AngpriakeCreature(BaseCreature):
    ...


class _AngpriakeVillageCreature(_AngpriakeCreature):
    ...


class _AngpriakeChurchCreature(_AngpriakeCreature):
    ...


class _AngpriakeCapitalCityCreature(_AngpriakeCreature):
    ...


class _AngpriakeForestCreature(_AngpriakeCreature):
    ...


class AngpriakeWorld(BaseWorld):
    name = "Angpriake"
    description = "The world dominated by the angels"
    id = 1
    location = _AngpriakeLocation
    ptype = _AngpriakePlayer
    event = _AngpriakeEvent


class Village(_AngpriakeLocation):
    name = "Village"
    description = "The village where you were born. You can earn `💲10`/h here"
    id = 0
    world = AngpriakeWorld
    coordination = Coordination(x=0, y=0)
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


class Church(_AngpriakeLocation):
    name = "Church"
    description = "The church near the village. You can change your character's class here."
    id = 1
    world = AngpriakeWorld
    coordination = Coordination(x=50, y=50)
    creature = _AngpriakeChurchCreature
    level_limit = 10
    class_changable = True


class CapitalCity(_AngpriakeLocation):
    name = "Capital City"
    description = "The capital city of the country"
    id = 2
    world = AngpriakeWorld
    coordination = Coordination(x=500, y=600)
    creature = _AngpriakeCapitalCityCreature
    level_limit = 20


class Forest(_AngpriakeLocation):
    name = "Forest"
    description = "The forest near the village"
    id = 3
    world = AngpriakeWorld
    coordination = Coordination(x=20, y=10)
    creature = _AngpriakeForestCreature


class Villager(_AngpriakePlayer):
    @classmethod
    @property
    def type_id(self) -> int:
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
    def type_id(self) -> int:
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


class Rabbit(_AngpriakeForestCreature):
    name = "Rabbit"
    description = "Rabbits are common in the Angpriake forest. You can find them anywhere."
    display = "🐇"
    exp = 5

    @property
    def hp_max(self) -> int:
        return 20

    @property
    def physical_atk(self) -> int:
        return 5

    @property
    def magical_atk(self) -> int:
        return 0

    @property
    def physical_res(self) -> float:
        return 0.7

    @property
    def magical_res(self) -> float:
        return 0.0

    @property
    def crit_rate(self) -> float:
        return 0.2

    @property
    def crit_dmg(self) -> float:
        return 0.3


class Eagle(_AngpriakeForestCreature):
    name = "Eagle"
    description = "A flying bird with high physical attack."
    display = "🦅"
    exp = 30

    @property
    def hp_max(self) -> int:
        return 30

    @property
    def physical_atk(self) -> int:
        return 12

    @property
    def magical_atk(self) -> int:
        return 0

    @property
    def physical_res(self) -> float:
        return 0.3

    @property
    def magical_res(self) -> float:
        return 0.3

    @property
    def crit_rate(self) -> float:
        return 0.45

    @property
    def crit_dmg(self) -> float:
        return 0.9

    def attack(self, target: Battleable) -> int:
        return self.physical_attack(target)


class Elephant(_AngpriakeForestCreature):
    name = "Elephant"
    description = "A giant animal with great HP."
    display = "🐘"
    exp = 200

    @property
    def hp_max(self) -> int:
        return 100

    @property
    def physical_atk(self) -> int:
        return 25

    @property
    def magical_atk(self) -> int:
        return 0

    @property
    def physical_res(self) -> float:
        return 0.7

    @property
    def magical_res(self) -> float:
        return 0.5

    @property
    def crit_rate(self) -> float:
        return 0.3

    @property
    def crit_dmg(self) -> float:
        return 1.2

    def attack(self, target: Battleable) -> int:
        return self.physical_attack(target)
