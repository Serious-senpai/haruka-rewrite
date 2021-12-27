from __future__ import annotations

import json
from typing import Any, Dict, Type, TypeVar, TYPE_CHECKING

import discord

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
    async def effect(cls: Type[HPT], user: PT, channel: discord.TextChannel) -> PT:
        user = await super().effect(user, channel)
        user.hp += cls.heal
        if user.hp > user.hp_max:
            user.hp = user.hp_max
        await user.save(hp=user.hp)
        await channel.send(f"<@!{user.id}> used **{cls.name}** and revived {cls.heal} HP!")
        return user


class CommonHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class RareHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class EpicHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class LegendaryHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...
class EXHealingPotion(BaseHealingPotion, JSONMetaObject, meta=meta): ...


class TeleportDevice(BaseItem, JSONMetaObject, meta=meta):
    @classmethod
    async def effect(cls: Type[TeleportDevice], user: PT, channel: discord.TextChannel, target: Type[LT] = None) -> PT:
        if target is None:
            # We are being invoked via $use
            await channel.send("Please use the `teleport` command instead!")
            return user

        if user.level < target.level_limit:
            await channel.send(f"You must reach `Lv.{target.level_limit}` to get access to this location!")
            return user

        if target.id == user.location.id:
            await channel.send(f"You have already been in **{target.name}**, cannot perform teleportation!")
            return user

        if user.traveling():
            await channel.send("You are currently traveling. Please get to the destination first!")
            return user

        if user.battling():
            await channel.send("Please complete your ongoing battle first!")
            return user

        user = await super().effect(user, channel, target)
        user = await user.location.on_leaving(user)
        user.location = target
        user = await user.location.on_arrival(user)
        await user.update()
        await channel.send(f"<@!{user.id}> teleported to **{target.name}**!")
        return user
