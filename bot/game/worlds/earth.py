from __future__ import annotations

import asyncio
import contextlib
from typing import Type, TypeVar

import discord

from ..combat import BattleResult, battle
from ..core import (
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
    Coordination,
)
from ..player import PT, BasePlayer


ELT = TypeVar("ELT", bound="_EarthLocation")
EET = TypeVar("EET", bound="_EarthEvent")
ECT = TypeVar("ECT", bound="_EarthCreature")
EPT = TypeVar("EPT", bound="_EarthPlayer")


class _EarthLocation(BaseLocation):
    ...


class _EarthEvent(BaseEvent):
    ...


class _EarthPlayer(BasePlayer):
    ...


class _EarthCreature(BaseCreature):
    ...


class _EarthHomeCreature(_EarthCreature):
    ...


class _EarthHighSchoolCreature(_EarthCreature):
    ...


class EarthWorld(BaseWorld):
    name = "Earth"
    description = "The world where we are all living in.\nYour journey starts from here."
    id = 0
    location = _EarthLocation
    ptype = _EarthPlayer
    event = _EarthEvent


class Home(_EarthLocation):
    name = "Home"
    description = "Your house where you are living alone."
    id = 0
    world = EarthWorld
    coordination = Coordination(x=0, y=0)
    creature = _EarthHomeCreature


class HighSchool(_EarthLocation):
    name = "High School"
    description = "The high school you are going to"
    id = 1
    world = EarthWorld
    coordination = Coordination(x=20, y=20)
    creature = _EarthHighSchoolCreature


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


class God(_EarthCreature):
    name = "God"
    description = "An unknown god that appeared out of nowhere and told you to reincarnate into another world"
    display = "😇"
    exp = 9999999

    @property
    def hp_max(self) -> int:
        return 25000

    @property
    def physical_atk(self) -> int:
        return 10000

    @property
    def magical_atk(self) -> int:
        return 10000

    @property
    def physical_res(self) -> float:
        return 0.0

    @property
    def magical_res(self) -> float:
        return 0.0

    @property
    def crit_rate(self) -> float:
        return 0.0

    @property
    def crit_dmg(self) -> float:
        return 0.0


class IsekaiEvent(_EarthEvent):
    name = "Isekai Event"
    description = "The beginning of the story"
    location = Home
    rate = 1.0

    @classmethod
    async def run(
        cls: Type[IsekaiEvent],
        target: discord.PartialMessageable,
        player: PT,
    ) -> PT:
        async with player.prepare_battle():
            with contextlib.suppress(discord.HTTPException):
                await target.send(embed=cls.create_embed(player))

            result: BattleResult = await battle(player, God())
            with contextlib.suppress(discord.HTTPException):
                async with target.typing():
                    await asyncio.sleep(2.0)
                    await result.send(target)

            return await player.from_user(player.user)
