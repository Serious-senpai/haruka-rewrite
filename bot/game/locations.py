from __future__ import annotations

import asyncio
import asyncpg
from typing import Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import LT
    from .player import PT


class MoneyStonksLocationMixin:
    stonk_per_hour: int
    tasks: Dict[int, asyncio.Task] = {}

    @classmethod
    async def _stonks(cls: Type[LT], conn: asyncpg.Pool, id: int) -> None:
        while await asyncio.sleep(3600 / cls.stonk_per_hour, True):
            await conn.execute(f"UPDATE rpg SET money = money + 1 WHERE id = '{id}';")

    @classmethod
    async def on_leaving(cls: Type[LT], player: PT) -> PT:
        cls.tasks[player.id].cancel()
        return player

    @classmethod
    async def on_arrival(cls: Type[LT], player: PT) -> PT:
        cls.tasks[player.id] = asyncio.create_task(cls._stonks(player.user._state.conn, player.id))
        return player
