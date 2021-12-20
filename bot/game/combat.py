from __future__ import annotations

import enum
from typing import NamedTuple, Tuple, TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from .core import CT
    from .player import PT


class BattleStatus(enum.Enum):
    WIN: int = 0
    LOSS: int = 1
    DRAW: int = 2

    def is_dead(self) -> bool:
        if self == self.WIN:
            return False
        return True


class BattleResult(NamedTuple):
    embed: discord.Embed
    player: PT
    status: BattleStatus
    leveled_up: bool


async def battle(player: PT, enemy: CT) -> BattleResult:
    """This function is a coroutine

    Calculate battle results

    Parameters
    -----
    player: :class:`BasePlayer`
        The player engaging the battle
    enemy: :class:`BaseCreature`
        The opponent

    Returns
    -----
    :class:`BattleResult`
        The result of the battle
    """
    turn: int = 0
    status: BattleStatus
    entities: Tuple[PT, CT] = (player, enemy)

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
    elif status == BattleStatus.LOSS:
        embed.color = 0xED4245
        embed.set_footer(text=f"{enemy.name} won")
    else:
        embed.color = 0x95a5a6
        embed.set_footer(text="Both of you died")

    if turn == 1:
        embed._footer["text"] += f" after {turn} turn!"
    else:
        embed._footer["text"] += f" after {turn} turns!"

    leveled_up: bool = False
    if status.is_dead():
        player = await player.isekai()
    else:
        leveled_up = player.gain_xp(enemy.exp)
        if leveled_up:
            player.hp = player.hp_max
        await player.update()

    return BattleResult(embed, player, status, leveled_up)


async def handler(target: discord.TextChannel, *, player: PT, enemy: CT) -> PT:
    """This function is a coroutine

    A higher level function than :func:`battle` that handles
    the battle results.
    """
    embed, player, status, leveled_up = await battle(player, enemy)

    if status.is_dead():
        await player.isekai_notify(target, embed=embed)
    elif leveled_up:
        await player.leveled_up_notify(target, embed=embed)
    else:
        await target.send(embed=embed)

    return player
