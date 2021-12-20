from __future__ import annotations

import asyncio
from typing import Type, TypeVar

import discord

from ..battle import battle
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
    pass


class _EarthEvent(BaseEvent):
    pass


class _EarthCreature(BaseCreature):
    pass


class _EarthPlayer(BasePlayer):
    pass


class _EarthHomeCreature(_EarthCreature):
    pass


class _EarthHighSchoolCreature(_EarthCreature):
    pass


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
    name = "God"
    description = "An unknown god that appeared out of nowhere and told you to reincarnate into another world"
    display = "😇"
    rate = 1.0

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
        target: discord.TextChannel,
        player: PT,
    ) -> None:
        user: discord.User = discord.User(state=target._state, data=await target._state.http.get_user(player.id))
        embed: discord.Embed = cls.create_embed(target._state)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
        message: discord.Message = await target.send(embed=embed)
        await asyncio.sleep(3.0)
        await message.edit(embed=battle(player, God()))

        if player.hp == 0:
            player.isekai()
        else:
            level_up: bool = player.gain_xp(9999999)
            if level_up:
                await target.send(f"<@!{player.id}> leveled up to Lv.{player.level}")

        await player.update(target._state.conn)
