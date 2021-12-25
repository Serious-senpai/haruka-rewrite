from __future__ import annotations

import json
from typing import Any, Dict, Optional, Type, TypeVar, TYPE_CHECKING

from .abc import JSONMetaObject
from .player import BaseItem
if TYPE_CHECKING:
    from .core import LT
    from .player import PT


with open("./bot/game/items.json", "r") as f:
    meta: Dict[str, Dict[str, Any]] = json.load(f)


HPT = TypeVar("HPT", bound="BaseHealingPotion")


class BaseHealingPotion(BaseItem):
    heal: int

    @classmethod
    async def effect(cls: Type[HPT], user: PT) -> None:
        await super().effect(user)
        user.hp += cls.heal
        if user.hp > user.hp_max:
            user.hp = user.hp_max
        await user.update(hp=user.hp)


class CommonHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class RareHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class EpicHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class LegendaryHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class EXHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...


class TeleportDevice(BaseItem, JSONMetaObject, meta=meta):
    @classmethod
    async def effect(cls: Type[TeleportDevice], user: PT, target: Type[LT]) -> Optional[LT]:
        if target.id == user.location.id:
            return

        await super().effect(user)
        user.location = target
        await user.update(location=target)
        return target
