import contextlib
from types import TracebackType
from typing import Literal, Optional, Type

import asyncpg

import haruka


class Database(contextlib.AbstractAsyncContextManager):

    __slots__ = (
        "bot",
        "database_url",
        "_pool",
    )

    def __init__(self, bot: haruka.Haruka, url: str) -> None:
        self.bot: haruka.Haruka = bot
        self.database_url: str = url

    async def __aenter__(self) -> asyncpg.Pool:
        await self.connect()
        return self._pool

    async def __aexit__(self, exc_type: Optional[Type[Exception]], exc_value: Optional[Exception], tb: Optional[TracebackType]) -> Literal[True]:
        return True

    async def connect(self) -> None:
        self._pool: asyncpg.Pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            max_inactive_connection_lifetime=3.0,
        )
        self.bot.log("Created connection pool.")
        await self.initialization()

    async def initialization(self) -> None:
        await self._pool.execute("""
            CREATE TABLE IF NOT EXISTS prefix (id text, pref text);
            CREATE TABLE IF NOT EXISTS youtube (id text, queue text[]);
            CREATE TABLE IF NOT EXISTS misc (title text, id text[]);
            CREATE TABLE IF NOT EXISTS remind (id text, time timestamptz, content text, url text, original timestamptz);
            CREATE TABLE IF NOT EXISTS muted (member text, guild text, time timestamptz, roles text[]);
            CREATE TABLE IF NOT EXISTS playlist (id SERIAL PRIMARY KEY, author_id text, title text, description text, queue text[], use_count integer);
            CREATE TABLE IF NOT EXISTS rpg (id text, description text, world int, location int, type int, level int, xp int, money int, items text, hp int, travel timestamptz, state text);
        """)

        for extension in (
            "pg_trgm",
        ):
            try:
                await self._pool.execute(f"CREATE EXTENSION {extension};")
            except BaseException:
                pass

        # Initialize blacklist
        if not await self._pool.fetchrow("SELECT * FROM misc WHERE title = 'blacklist';"):
            await self._pool.execute("INSERT INTO misc VALUES ('blacklist', $1);", [])
            self.bot.log("Created new blacklist.")
        else:
            self.bot.log("Existing blacklist found.")

        self.bot.log("Successfully initialized database.")
