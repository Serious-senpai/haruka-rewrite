from __future__ import annotations

import json
from typing import Any, Dict, Type, TypeVar

from game.abc import Battleable, JSONMetaObject
from game.core import (
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
)
from game.player import BasePlayer
from game.locations import MoneyStonksLocationMixin


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
class _AngpriakeWorldCenterCreature(_AngpriakeCreature): ...


class AngpriakeWorld(BaseWorld, JSONMetaObject, meta=meta):
    location = _AngpriakeLocation
    ptype = _AngpriakePlayer
    event = _AngpriakeEvent


class Village(MoneyStonksLocationMixin, _AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeVillageCreature


class Church(_AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeChurchCreature


class CapitalCity(MoneyStonksLocationMixin, _AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeCapitalCityCreature


class Forest(_AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeForestCreature


class WorldCenter(_AngpriakeLocation, JSONMetaObject, meta=meta):
    world = AngpriakeWorld
    creature = _AngpriakeWorldCenterCreature


class Duck(_AngpriakeForestCreature, JSONMetaObject, meta=meta): ...
class Rabbit(_AngpriakeForestCreature, JSONMetaObject, meta=meta): ...


class Eagle(_AngpriakeForestCreature, JSONMetaObject, meta=meta):
    def attack(self, target: Battleable) -> int:
        return self.physical_attack(target)


class Elephant(_AngpriakeForestCreature, JSONMetaObject, meta=meta):
    def attack(self, target: Battleable) -> int:
        return self.physical_attack(target)


class Thief(_AngpriakeCapitalCityCreature, JSONMetaObject, meta=meta): ...
class Angel(_AngpriakeWorldCenterCreature, JSONMetaObject, meta=meta): ...


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
        return self.level / (self.level + 10)

    @property
    def crit_rate(self) -> float:
        return 0.5

    @property
    def crit_dmg(self) -> float:
        return 0.8

    def attack(self, target: Battleable) -> int:
        return self.magical_attack(target)


class Assassin(_AngpriakePlayer):
    @classmethod
    @property
    def display(cls: Type[Assassin]) -> str:
        return "🥷"

    @classmethod
    @property
    def type_id(cls: Type[Assassin]) -> int:
        return 3

    @property
    def hp_max(self) -> int:
        return 100 + self.level

    @property
    def physical_atk(self) -> int:
        return 50 + 5 * self.level

    @property
    def magical_atk(self) -> int:
        return 50 + 4 * self.level

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 20)

    @property
    def magical_res(self) -> float:
        return self.level / (self.level + 25)

    @property
    def crit_rate(self) -> float:
        return 0.9

    @property
    def crit_dmg(self) -> float:
        return self.level / (self.level + 5)
