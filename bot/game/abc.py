from __future__ import annotations

import json
import random
from typing import Any, Dict, Type

import discord


__all__ = (
    "Battleable",
    "ClassObject",
    "JSONMetaObject",
)


class ClassObject:
    """Base class for objects that shouldn't be represented
    by class instances.
    """

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("This object is represented by the class itself")


class Battleable:
    """An ABC that implements common operations for an entity which can battle."""

    hp_max: int
    physical_atk: int
    magical_atk: int
    physical_res: float
    magical_res: float
    crit_rate: float
    crit_dmg: float

    def _criticalize(self, dmg: float) -> float:
        if random.random() < self.crit_rate:
            return dmg * (1 + self.crit_dmg)
        return dmg

    def attack(self, target: Battleable) -> int:
        """Perform a physical or magical attack to another entity

        The attack type will be chosen at random

        Parameters
        -----
        target: :class:`Battleable`
            The attacked target

        Returns
        :class:`int`
            The damage dealt. This cannot be lower than 0.
        """
        if random.random() < 0.5:
            return self.physical_attack(target)
        else:
            return self.magical_attack(target)

    def physical_attack(self, target: Battleable) -> int:
        """Perform a physical attack to another entity.

        This method also takes items' effects as well as target's resistance
        point in account and returns the damage dealt (minimum 0).

        Parameters
        -----
        target: :class:`Battleable`
            The attacked target

        Returns
        :class:`int`
            The damage dealt. This cannot be lower than 0.
        """
        _dmg: float = self.physical_atk * (1 - target.physical_res)
        _dmg = self._criticalize(_dmg)

        dmg: int = max(0, int(_dmg))
        target.hp -= dmg
        return dmg

    def magical_attack(self, target: Battleable) -> int:
        """Perform a magical attack to another entity.

        This method also takes items' effects as well as target's resistance
        point in account and returns the damage dealt (minimum 0).

        Parameters
        -----
        target: :class:`Battleable`
            The attacked target

        Returns
        :class:`int`
            The damage dealt. This cannot be lower than 0.
        """
        _dmg: float = self.magical_atk * (1 - target.magical_res)
        _dmg = self._criticalize(_dmg)

        dmg: int = max(0, int(_dmg))
        target.hp -= dmg
        return dmg

    def append_status(self, embed: discord.Embed) -> discord.Embed:
        embed.add_field(
            name="Physical ATK",
            value=self.physical_atk,
        )
        embed.add_field(
            name="Magical ATK",
            value=self.magical_atk,
        )
        embed.add_field(
            name="Physical RES",
            value="{:.2f}%".format(100 * self.physical_res),
        )
        embed.add_field(
            name="Magical RES",
            value="{:.2f}%".format(100 * self.magical_res),
        )
        embed.add_field(
            name="CRIT Rate",
            value="{:.2f}%".format(100 * self.crit_rate),
        )
        embed.add_field(
            name="CRIT DMG",
            value="{:.2f}%".format(100 * self.crit_dmg),
        )
        return embed


class JSONMetaObject:
    def __init_subclass__(cls: Type, /, meta: Dict[str, Dict[str, Any]], **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        data: Dict[str, Any] = meta[cls.__name__]
        for key, value in data.items():
            setattr(cls, key, value)
