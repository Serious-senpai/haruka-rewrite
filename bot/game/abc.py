from __future__ import annotations


__all__ = (
    "Battleable",
)


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
        """The percentage of reduced incoming physical damage."""
        raise NotImplementedError

    @property
    def magical_res(self) -> float:
        """The percentage of reduced incoming magical damage."""
        raise NotImplementedError

    def physical_attack(self, target: Battleable) -> int:
        """Perform a physical attack to another entity.

        This method also takes items' effects as well as target's resistance
        point and returns the damage dealt (minimum 0).

        Parameters
        -----
        target: :class:`Battleable`
            The attacked target

        Returns
        :class:`int`
            The damage dealt. This cannot be lower than 0.
        """
        dmg: int = int(self.physical_atk * (1 - target.physical_res))
        target.hp -= dmg
        return dmg

    def magical_attack(self, target: Battleable) -> int:
        """Perform a magical attack to another entity.

        This method also takes items' effects as well as target's resistance
        point and returns the damage dealt (minimum 0).

        Parameters
        -----
        target: :class:`Battleable`
            The attacked target

        Returns
        :class:`int`
            The damage dealt. This cannot be lower than 0.
        """
        dmg: int = int(self.magical_atk * (1 - target.magical_res))
        target.hp -= dmg
        return dmg
