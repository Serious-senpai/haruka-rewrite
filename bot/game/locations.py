from __future__ import annotations

import asyncio
import asyncpg
from typing import Dict, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import PT


MST = TypeVar("MST", bound="MoneyStonksLocationBase")
HDT = TypeVar("HDT", bound="HPDepletionLocationBase")


class MoneyStonksLocationBase:
    """Base class for locations that increase players' money regularly.

    Subclasses must implement the ``stonk_per_hour`` class attribute.
    """
    stonk_per_hour: int
    tasks: Dict[int, asyncio.Task] = {}

    def __init_subclass__(cls: Type[MST], **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        try:
            assert hasattr(cls, "stonk_per_hour")
        except AssertionError as exc:
            raise RuntimeError(f"Missing required attribute for {cls.__name__}") from exc

    @classmethod
    async def _stonks(cls: Type[MST], conn: asyncpg.Pool, id: int) -> None:
        while await asyncio.sleep(3600 / cls.stonk_per_hour, True):
            await conn.execute(f"UPDATE rpg SET money = money + 1 WHERE id = '{id}';")

    @classmethod
    async def on_arrival(cls: Type[MST], player: PT) -> PT:
        cls.tasks[player.id] = asyncio.create_task(cls._stonks(player.user._state.conn, player.id))
        return player

    @classmethod
    async def on_leaving(cls: Type[MST], player: PT) -> PT:
        cls.tasks[player.id].cancel()
        return player


class HPDepletionLocationBase:
    """Base class for locations that deplete players' HP regularly.

    Subclasses must implement the ``deplete_per_hour`` class attribute.
    """
    deplete_per_hour: int
    tasks: Dict[int, asyncio.Task] = {}

    def __init_subclass__(cls: Type[HDT], **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        try:
            assert hasattr(cls, "deplete_per_hour")
        except AssertionError as exc:
            raise RuntimeError(f"Missing required attribute for {cls.__name__}") from exc

    @classmethod
    async def _deplete(cls: Type[HDT], conn: asyncpg.Pool, id: int) -> None:
        while await asyncio.sleep(3600 / cls.deplete_per_hour, True):
            await conn.execute(f"UPDATE rpg SET hp = hp - 1 WHERE id = '{id}';")

    @classmethod
    async def on_arrival(cls: Type[HDT], player: PT) -> PT:
        cls.tasks[player.id] = asyncio.create_task(cls._deplete(player.user._state.conn, player.id))
        return player

    @classmethod
    async def on_leaving(cls: Type[HDT], player: PT) -> PT:
        cls.tasks[player.id].cancel()
        return player
