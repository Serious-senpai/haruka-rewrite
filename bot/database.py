import asyncio
import contextlib
import traceback
from types import TracebackType
from typing import Literal, Optional, Type

import asyncpg


class Database(contextlib.AbstractAsyncContextManager):

    __slots__ = (
        "bot",
        "database_url",
        "_pool",
    )

    def __init__(self, bot, url):
        self.bot = bot
        self.database_url: str = url

    async def __aenter__(self) -> asyncpg.Pool:
        await self.connect()
        return self._pool

    async def __aexit__(self, exc_type: Optional[Type[Exception]], exc_value: Optional[Exception], tb: Optional[TracebackType]) -> Literal[True]:
        if exc_value:
            self.bot.log("".join(line for line in traceback.format_exception(exc_type, exc_value, tb)))

        try:
            await asyncio.wait_for(self._pool.close(), timeout = 10.0)
        except:
            self.bot.log("Unable to close database connection.")
            self.bot.log(traceback.format_exc())
        else:
            self.bot.log("Successfully closed database connection.")

        return True

    async def connect(self) -> None:
        self._pool: asyncpg.Pool = await asyncpg.create_pool(
            self.database_url,
            min_size = 10,
            max_size = 10,
            max_inactive_connection_lifetime = 3.0,
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
            CREATE TABLE IF NOT EXISTS snipe (channel_id text, message_id text, content text, author_id text, attachments text[]);
            CREATE TABLE IF NOT EXISTS playlist (id SERIAL PRIMARY KEY, author_id text, title text, description text, queue text[], use_count integer);
        """)

        for extension in (
            "fuzzystrmatch",
            "pg_trgm",
        ):
            try:
                await self._pool.execute(f"CREATE EXTENSION {extension};")
            except:
                pass


        # Initialize blacklist
        if not await self._pool.fetchrow("SELECT * FROM misc WHERE title = 'blacklist';"):
            await self._pool.execute("INSERT INTO misc VALUES ('blacklist', $1);", [])
            self.bot.log("Created new blacklist.")
        else:
            self.bot.log("Existing blacklist found.")

        self.bot.log("Successfully initialized database.")
