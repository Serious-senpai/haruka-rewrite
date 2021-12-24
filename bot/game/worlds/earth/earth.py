from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any, Dict, Type, TypeVar

import discord

from game.abc import JSONMetaObject
from game.combat import BattleResult, battle
from game.core import (
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
    Coordination,
)
from game.player import PT, BasePlayer


__all__ = (
    "EarthWorld",
    "Home",
    "HighSchool",
    "Student",
    "God",
    "IsekaiEvent",
)


ELT = TypeVar("ELT", bound="_EarthLocation")
EET = TypeVar("EET", bound="_EarthEvent")
ECT = TypeVar("ECT", bound="_EarthCreature")
EPT = TypeVar("EPT", bound="_EarthPlayer")


with open("./bot/game/worlds/earth/earth.json", "r", encoding="utf-8") as f:
    meta: Dict[str, Dict[str, Any]] = json.load(f)


class _EarthLocation(BaseLocation): ...
class _EarthEvent(BaseEvent): ...
class _EarthPlayer(BasePlayer): ...
class _EarthCreature(BaseCreature): ...
class _EarthHomeCreature(_EarthCreature): ...
class _EarthHighSchoolCreature(_EarthCreature): ...


class EarthWorld(BaseWorld, JSONMetaObject, meta=meta):
    location = _EarthLocation
    ptype = _EarthPlayer
    event = _EarthEvent


class Home(_EarthLocation, JSONMetaObject, meta=meta):
    world = EarthWorld
    coordination = Coordination(x=0, y=0)
    creature = _EarthHomeCreature


class HighSchool(_EarthLocation, JSONMetaObject, meta=meta):
    world = EarthWorld
    coordination = Coordination(x=20, y=20)
    creature = _EarthHighSchoolCreature


class God(_EarthHomeCreature, JSONMetaObject, meta=meta): ...


class IsekaiEvent(_EarthEvent, JSONMetaObject, meta=meta):
    location = Home

    @classmethod
    async def run(
        cls: Type[IsekaiEvent],
        target: discord.PartialMessageable,
        player: PT,
    ) -> PT:
        async with player.prepare_battle():
            await super().run(target, player)

            result: BattleResult = await battle(player, God())
            with contextlib.suppress(discord.HTTPException):
                async with target.typing():
                    await asyncio.sleep(2.0)
                    await result.send(target)

            player.release()
            return await player.from_user(player.user)


class Student(_EarthPlayer):
    @classmethod
    @property
    def type_id(self) -> int:
        return 0

    @property
    def hp_max(self) -> int:
        return 100 + self.level

    @property
    def physical_atk(self) -> int:
        return 2 + self.level

    @property
    def magical_atk(self) -> int:
        return 0

    @property
    def physical_res(self) -> float:
        return self.level / (self.level + 20)

    @property
    def magical_res(self) -> float:
        return 0.0

    @property
    def crit_rate(self) -> float:
        return 0.0005

    @property
    def crit_dmg(self) -> float:
        return 9999
