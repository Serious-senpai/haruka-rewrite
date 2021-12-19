from __future__ import annotations

import random


__all__ = (
    "Battleable",
    "ClassObject",
)


class ClassObject:
    """Base class for objects that shouldn't be represented
    by class instances.
    """
    def __init__(self, *args, **kwargs) -> None:
        raise TypeError("This object is represented by the class itself")


class Battleable:
    """An ABC that implement common operations for an entity which can battle."""

    @property
    def hp_max(self) -> int:
        """The maximum health point of the entity."""
        raise NotImplementedError

    @property
    def physical_atk(self) -> int:
        """The physical attack point of the entity."""
        raise NotImplementedError

    @property
    def magical_atk(self) -> int:
        """The magical attack point of the entity."""
        raise NotImplementedError

    @property
    def physical_res(self) -> float:
        """The percentage of reduced incoming physical damage (range 0 - 1)"""
        raise NotImplementedError

    @property
    def magical_res(self) -> float:
        """The percentage of reduced incoming magical damage (range 0 - 1)"""
        raise NotImplementedError

    @property
    def crit_rate(self) -> float:
        """The critical damage rate (range 0 - 1)"""
        raise NotImplementedError

    @property
    def crit_dmg(self) -> float:
        """The critical damage multiplier (initial damage is scaled to 1)"""
        raise NotImplementedError

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
