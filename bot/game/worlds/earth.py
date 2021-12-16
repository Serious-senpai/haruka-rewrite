from __future__ import annotations

from typing import List, Type

import discord

from ..abc import Battleable
from ..battle import battle
from ..core import (
    WT,
    MISSING,
    BaseWorld,
    BaseLocation,
    BaseEvent,
    BaseCreature,
    Coordination,
)
from ..player import BasePlayer


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
    locations: List[_EarthLocation] = MISSING
    ptypes: List[_EarthPlayer] = MISSING
    events: List[_EarthEvent] = MISSING


class Home(_EarthLocation):
    name: str = "Home"
    description: str = "Your house where you are living alone."
    id: int = 0
    world: Type[WT] = EarthWorld
    coordination: Coordination = Coordination(x=0, y=0)
    creatures: List[Type[_EarthCreature]] = []


class HighSchool(_EarthLocation):
    name: str = "High School"
    description: str = "The high school you are going to"
    id: int = 1
    world: Type[WT] = EarthWorld
    coordination: Coordination = Coordination(x=20, y=20)
    creatures: List[Type[_EarthCreature]] = MISSING


class Student(_EarthPlayer):
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
    location: Type[_EarthLocation] = Home
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
    world: Type[WT] = EarthWorld
    rate: float = 1

    @classmethod
    async def run(
        cls: Type[IsekaiEvent],
        target: discord.TextChannel,
        player: Student,
    ) -> None:
        god: God = God()
        await target.send(embed=battle(player, god))


EarthWorld.locations = [Home, HighSchool]
EarthWorld.ptypes = [Student]
EarthWorld.events = [IsekaiEvent]
HighSchool.creatures = [God]
