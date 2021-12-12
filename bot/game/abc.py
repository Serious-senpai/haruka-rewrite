from __future__ import annotations


__all__ = (
    "Battleable",
)


class Battleable:
    """An ABC that implement common operations for an entity
    that can battle.
    """

    def physical_attack(self, enemy: Battleable) -> int:
        dmg: int = self.physical_atk
        enemy.hp -= dmg
        return dmg

    def magical_atk(self, enemy: Battleable) -> int:
        dmg: int = self.magical_atk
        enemy.hp -= dmg
        return dmg
