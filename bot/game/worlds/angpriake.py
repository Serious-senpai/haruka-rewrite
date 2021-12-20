from __future__ import annotations

import asyncio
from typing import Type, TypeVar

import discord

from ..battle import battle
from ..core import (
    WT,
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


class _AngpriakeLocation(BaseLocation): ...

class _AngpriakeEvent(BaseEvent): ...

class _AngpriakePlayer(BasePlayer): ...

class _AngpriakeCreature(BaseCreature): ...
class _AngpriakeVillageCreature(_AngpriakeCreature): ...
class _AngpriakeChurchCreature(_AngpriakeCreature): ...
class _AngpriakeCapitalCityCreature(_AngpriakeCreature): ...


class AngpriakeWorld(BaseWorld):
    name = "Angpriake"
    description = "The world dominated by the angels"
    id = 1
    location = _AngpriakeLocation
    ptype = _AngpriakePlayer
    event = _AngpriakeEvent


class Village(_AngpriakeLocation):
    name = "Village"
    description = "The village where you were born"
    id = 0
    world = AngpriakeWorld
    coordination = Coordination(x=0, y=0)
    creature = _AngpriakeVillageCreature


class Church(_AngpriakeLocation):
    name = "Church"
    description = "The church near the village. You can change your character's class here."
    id = 1
    world = AngpriakeWorld
    coordination = Coordination(x=50, y=50)
    creature = _AngpriakeChurchCreature
    level_limit = 10


class CapitalCity(_AngpriakeLocation):
    name = "Capital City"
    description = "The capital city of the country"
    id = 2
    world = AngpriakeWorld
    coordination = Coordination(x=500, y=600)
    creature = _AngpriakeCapitalCityCreature
    level_limit = 20


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
