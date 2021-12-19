from __future__ import annotations

from typing import List, Type, TypeVar

import discord

from ..battle import battle
from ..core import (
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
    Coordination,
)
from ..player import BasePlayer


ELT = TypeVar("ELT", bound="_EarthLocation")
EET = TypeVar("EET", bound="_EarthEvent")
ECT = TypeVar("ECT", bound="_EarthCreature")
EPT = TypeVar("EPT", bound="_EarthPlayer")


class _EarthLocation(BaseLocation):
    pass


class _EarthEvent(BaseEvent):
    pass


class _EarthCreature(BaseCreature):
    pass


class _EarthPlayer(BasePlayer):
    pass


class EarthWorld(BaseWorld):
    name: str = "Earth"
    description: str = "The world where we are all living in.\nYour journey starts from here."
    id: int = 0
    locations: List[Type[ELT]] = _EarthLocation.__subclasses__
    ptypes: List[Type[EPT]] = _EarthPlayer.__subclasses__
    events: List[Type[EET]] = _EarthEvent.__subclasses__


class Home(_EarthLocation):
    name: str = "Home"
    description: str = "Your house where you are living alone."
    id: int = 0
    world: Type[EarthWorld] = EarthWorld
    coordination: Coordination = Coordination(x=0, y=0)
    creatures: List[Type[ECT]] = _EarthCreature.__subclasses__


class HighSchool(_EarthLocation):
    name: str = "High School"
    description: str = "The high school you are going to"
    id: int = 1
    world: Type[EarthWorld] = EarthWorld
    coordination: Coordination = Coordination(x=20, y=20)
    creatures: List[Type[ECT]] = []


class Student(_EarthPlayer):
    @property
    def type_id(self) -> int:
        return 0

    @property
    def hp_max(self) -> int:
        return 100

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
    name: str = "God"
    description: str = "An unknown god that appeared out of nowhere and told you to reincarnate into another world"
    location: Type[ELT] = Home
    display: str = "😇"

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
    name: str = "The special meeting"
    description: str = "The beginning of the story"
    world: Type[EarthWorld] = EarthWorld
    rate: float = 1.0

    @classmethod
    async def run(
        cls: Type[IsekaiEvent],
        target: discord.TextChannel,
        player: Student,
    ) -> None:
        god: God = God()
        await target.send(embed=battle(player, god))
