from __future__ import annotations

import json
from typing import Any, Dict, Type

from game.abc import Battleable, JSONMetaObject
from game.core import (
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
)
from game.player import BasePlayer
from game.locations import (
    HPDepletionLocationBase,
    MoneyStonksLocationBase,
)


with open("./bot/game/worlds/redrotdom/redrotdom.json", "r", encoding="utf-8") as f:
    meta: Dict[str, Dict[str, Any]] = json.load(f)


class _RedrotdomLocation(BaseLocation): ...
class _RedrotdomEvent(BaseEvent): ...
class _RedrotdomPlayer(BasePlayer): ...
class _RedrotdomCreature(BaseCreature): ...
class _RedrotdomVillageCreature(_RedrotdomCreature): ...
class _RedrotdomMiningCampCreature(_RedrotdomCreature): ...
class _RedrotdomMysticForestCreature(_RedrotdomCreature): ...
class _RedrotdomWorldCenterCreature(_RedrotdomCreature): ...


class RedrotdomWorld(BaseWorld, JSONMetaObject, meta=meta):
    location = _RedrotdomLocation
    ptype = _RedrotdomPlayer
    event = _RedrotdomEvent


class Village(MoneyStonksLocationBase, _RedrotdomLocation, JSONMetaObject, meta=meta):
    world = RedrotdomWorld
    creature = _RedrotdomVillageCreature


class MiningCamp(MoneyStonksLocationBase, _RedrotdomLocation, JSONMetaObject, meta=meta):
    world = RedrotdomWorld
    creature = _RedrotdomMiningCampCreature


class MysticForest(_RedrotdomLocation, JSONMetaObject, meta=meta):
    world = RedrotdomWorld
    creature = _RedrotdomMysticForestCreature


class WorldCenter(HPDepletionLocationBase, _RedrotdomLocation, JSONMetaObject, meta=meta):
    world = RedrotdomWorld
    creature = _RedrotdomWorldCenterCreature


class Greez(_RedrotdomMiningCampCreature, JSONMetaObject, meta=meta): ...
class Unmtron(_RedrotdomMiningCampCreature, _RedrotdomMysticForestCreature, JSONMetaObject, meta=meta): ...
class SupremeEnforcerCyborg(_RedrotdomMysticForestCreature, _RedrotdomWorldCenterCreature, JSONMetaObject, meta=meta): ...
class Unknown(_RedrotdomWorldCenterCreature, JSONMetaObject, meta=meta): ...


class RobotController(_RedrotdomPlayer):
    @classmethod
    @property
    def type_id(cls: Type[RobotController]) -> int:
        return 0

    @property
    def hp_max(self) -> int:
        return 110 + self.level

    @property
    def physical_atk(self) -> int:
        return 15 + 2 * self.level

    @property
    def magical_atk(self) -> int:
        return 14 + 2 * self.level

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 13)

    @property
    def magical_res(self) -> float:
        return self.level / (self.level + 15)

    @property
    def crit_rate(self) -> float:
        return self.level / (self.level + 15)

    @property
    def crit_dmg(self) -> float:
        return self.level / (self.level + 10)


class MachineHunter(_RedrotdomPlayer):
    @classmethod
    @property
    def display(cls: Type[MachineHunter]) -> str:
        return "💂"

    @classmethod
    @property
    def type_id(cls: Type[MachineHunter]) -> int:
        return 1

    @property
    def hp_max(self) -> int:
        return 200 + 3 * self.level

    @property
    def physical_atk(self) -> int:
        return 20 + 3 * self.level

    @property
    def magical_atk(self) -> int:
        return 18 + 3 * self.level

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 8)

    @property
    def magical_res(self) -> float:
        return self.level / (self.level + 10)

    @property
    def crit_rate(self) -> float:
        return self.level / (self.level + 5)

    @property
    def crit_dmg(self) -> float:
        return self.level / (self.level + 4)


class RobotMaster(_RedrotdomPlayer):
    @classmethod
    @property
    def display(cls: Type[RobotMaster]) -> str:
        return "💂"

    @classmethod
    @property
    def type_id(cls: Type[RobotMaster]) -> int:
        return 2

    @property
    def hp_max(self) -> int:
        return 150 + 2 * self.level

    @property
    def physical_atk(self) -> int:
        return 25 + 4 * self.level

    @property
    def magical_atk(self) -> int:
        return 23 + 4 * self.level

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 12)

    @property
    def magical_res(self) -> float:
        return self.level / (self.level + 15)

    @property
    def crit_rate(self) -> float:
        return self.level / (self.level + 10)

    @property
    def crit_dmg(self) -> float:
        return self.level / (self.level + 6)
