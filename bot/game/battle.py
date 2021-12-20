from __future__ import annotations

import enum
from typing import NamedTuple, Tuple, TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from .core import BaseCreature
    from .player import PT


__all__ = (
    "battle",
)


class BattleStatus(enum.Enum):
    WIN: int = 0
    LOSS: int = 1
    DRAW: int = 2


class BattleResult(NamedTuple):
    embed: discord.Embed
    player: PT


async def battle(player: PT, enemy: BaseCreature) -> BattleResult:
    turn: int = 0
    status: BattleStatus
    entities: Tuple[PT, BaseCreature] = (player, enemy)

    while player.hp > 0 and enemy.hp > 0:
        turn += 1
        for index, entity in enumerate(entities):
            target = entities[1 - index]
            entity.attack(target)

            if player.hp <= 0 or enemy.hp <= 0:  # The damage may be reflected somehow
                if player.hp > 0:
                    status = BattleStatus.WIN
                    enemy.hp = 0
                elif enemy.hp > 0:
                    status = BattleStatus.LOSS
                    player.hp = 0
                else:
                    status = BattleStatus.DRAW
                    player.hp = 0
                    enemy.hp = 0
                break

    embed: discord.Embed = discord.Embed()
    embed.set_author(name=f"⚔️ {player.name} challenged {enemy.name}")
    embed.add_field(
        name=f"{player.display} {player.name}",
        value=f"HP {player.hp}/{player.hp_max}",
        inline=True,
    )
    embed.add_field(
        name=f"{enemy.name} {enemy.display}",
        value=f"HP {enemy.hp}/{enemy.hp_max}",
        inline=True,
    )

    if status == BattleStatus.WIN:
        embed.color = 0x2ECC71
        embed.set_footer(text=f"{player.name} won")
        player.gain_xp(enemy.exp)
    elif status == BattleStatus.LOSS:
        embed.color = 0xED4245
        embed.set_footer(text=f"{enemy.name} won")
        player = await player.isekai()
    else:
        embed.color = 0x95a5a6
        embed.set_footer(text="Draw")

    if turn == 1:
        embed._footer["text"] += f" after {turn} turn!"
    else:
        embed._footer["text"] += f" after {turn} turns!"

    return BattleResult(embed, player)
