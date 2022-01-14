from __future__ import annotations

import asyncio
import contextlib
import traceback
from typing import Any, Optional, TYPE_CHECKING

import asyncpg
import discord
from discord.ext import tasks

if TYPE_CHECKING:
    import haruka


class Task:
    """Represents a future task

    Attributes
    -----
    bot: ``haruka.Haruka``
        The bot associated with this task
    conn: ``asyncpg.Pool``
        The database connection pool
    task: ``asyncio.Task``
        The underlying task for this object
    """

    def __init__(self, manager: TaskManager) -> None:
        self.bot: haruka.Haruka = manager.bot
        self.conn: asyncpg.Pool = manager.conn
        self.task: asyncio.Task = self.run.start()

    @tasks.loop()
    async def run(self) -> Any:
        raise NotImplementedError

    @run.before_loop
    async def prepare(self) -> None:
        await self.bot.wait_until_ready()

    @run.error
    async def _error_handler(self, *args) -> None:
        exc: Exception = args[-1]
        self.bot.log(f"Exception occured in module 'task': {self.__class__.__name__}")
        self.bot.log("".join(traceback.format_exception(exc.__class__, exc, exc.__traceback__)))
        await self.bot.report("An exception has just occurred in the `task` module", send_state=False)

    async def cleanup(self) -> Any:
        return

    def restart(self) -> None:
        self.run.restart()


class ReminderTask(Task):

    @tasks.loop()
    async def run(self) -> None:
        asyncio.current_task().set_name("ReminderTask")
        row: Optional[asyncpg.Record] = await self.conn.fetchrow("SELECT * FROM remind ORDER BY time LIMIT 1;")
        if not row:
            await asyncio.sleep(3600)
            return

        await discord.utils.sleep_until(row["time"])
        await self.delete(row)

        try:
            user: discord.User = await self.bot.fetch_user(row["id"])  # Union[str, int]
        except BaseException:
            return

        embed: discord.Embed = discord.Embed(
            description=row["content"],
            timestamp=row["original"],
        )
        embed.set_author(
            name=f"{user.name}, this is your reminder.",
            icon_url=self.bot.user.avatar.url,
        )
        embed.add_field(
            name="Original message URL",
            value=row["url"],
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)

        with contextlib.suppress(discord.Forbidden):
            await user.send(embed=embed)

    async def delete(self, row: asyncpg.Record) -> None:
        await self.conn.execute(
            "DELETE FROM remind WHERE id = $1 AND time = $2 AND original = $3;",
            row["id"], row["time"], row["original"],
        )


class TaskManager:
    """Represents the object that is
    responsible for managing all Tasks.

    Attributes
    -----
    bot: ``haruka.Haruka``
        The bot associated with this TaskManager.
    remind: ``ReminderTask``
        The running ``ReminderTask``
    """

    __slots__ = ("bot", "remind", "travel")
    if TYPE_CHECKING:
        bot: haruka.Haruka
        remind: ReminderTask

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self.remind = ReminderTask(self)

    @property
    def conn(self) -> asyncpg.Pool:
        """The connection or connection pool to connect to the
        database.

        This is the same as the database connection of the bot.
        """
        return self.bot.conn
