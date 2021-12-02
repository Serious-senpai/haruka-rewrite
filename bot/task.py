from __future__ import annotations

import asyncio
from typing import Any, List, Optional

import asyncpg
import discord
from discord.ext import tasks

import haruka


class Task:
    """Represents a future task

    Attributes
    -----
    bot: :class:`haruka.Haruka`
        The bot associated with this task
    conn: :class:`asyncpg.Pool`
        The database connection pool
    task: :class:`asyncio.Task`
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

    async def cleanup(self) -> Any:
        return

    def restart(self) -> None:
        self.run.restart()


class ReminderTask(Task):

    @tasks.loop()
    async def run(self) -> None:
        row: Optional[asyncpg.Record] = await self.conn.fetchrow("SELECT * FROM remind ORDER BY time;")
        if not row:
            await asyncio.sleep(3600)
            return
        
        await discord.utils.sleep_until(row["time"])
        await self.delete(row)

        try:
            user: discord.User = await self.bot.fetch_user(row["id"]) # Union[str, int]
        except:
            return

        em: discord.Embed = discord.Embed(
            description = row["content"],
            color = 0x2ECC71,
            timestamp = row["original"],
        )
        em.set_author(
            name = f"{user.name}, this is your reminder.",
            icon_url = self.bot.user.avatar.url,
        )
        em.add_field(
            name = "Original message URL",
            value = row["url"],
        )
        em.set_thumbnail(url = user.avatar.url if user.avatar else discord.Embed.Empty)

        try:
            await user.send(embed = em)
        except discord.Forbidden:
            pass

    async def delete(self, row: asyncpg.Record) -> None:
        await self.conn.execute(
            "DELETE FROM remind WHERE id = $1 AND time = $2 AND original = $3;",
            row["id"], row["time"], row["original"],
        )


class UnmuteTask(Task):

    @tasks.loop()
    async def run(self) -> None:
        row: Optional[asyncpg.Record] = await self.conn.fetchrow("SELECT * FROM muted ORDER BY time;")
        if not row:
            await asyncio.sleep(3600)
            return
        
        await discord.utils.sleep_until(row["time"])
        await self.unmute(row)

    async def unmute(self, row: asyncpg.Record, *, member: Optional[discord.Member] = None, reason: str = "Mute timed out") -> None:
        await self.delete(row)

        guild: Optional[discord.Guild] = self.bot.get_guild(int(row["guild"]))
        if not guild:
            return
        muted_role: Optional[discord.Role] = discord.utils.find(lambda r: r.name == "Muted by Haruka", guild.roles)

        try:
            if not member:
                member: discord.Member = await guild.fetch_member(row["member"]) # Union[str, int]
            await member.remove_roles(muted_role)
        except:
            pass

        if not member:
            return

        self.bot.loop.create_task(self.cleanup(member = member, reason = "Timed out"))
        roles: List[discord.Object] = [discord.Object(id) for id in row["roles"]]
        try:
            await member.add_roles(*roles, reason = "Unmute: " + reason[:50])
        except:
            pass

    async def cleanup(self, *, member: discord.Member, reason: str) -> None:
        em: discord.Embed = discord.Embed(
            color = 0x2ECC71,
            timestamp = discord.utils.utcnow(),
        )
        em.set_author(
            name = "You were unmuted from the server",
            icon_url = self.bot.user.avatar.url,
        )
        em.add_field(
            name = "Server",
            value = member.guild.name,
        )
        em.add_field(
            name = "Reason",
            value = reason,
        )
        em.set_thumbnail(url = member.guild.icon.url if member.guild.icon else discord.Embed.Empty)
        try:
            await member.send(embed = em)
        except discord.Forbidden:
            return

    async def delete(self, row: asyncpg.Record) -> None:
        await self.conn.execute(
            "DELETE FROM muted WHERE member = $1 AND guild = $2;",
            row["member"], row["guild"],
        )


class TaskManager:
    """Represents the object that is
    responsible for managing all Tasks.

    Attributes
    -----
    bot: :class:`haruka.Haruka`
        The bot associated with this TaskManager.
    remind: :class:`ReminderTask`
        The running :class:`ReminderTask`
    unmute: :class:`UnmuteTask`
        The running :class:`UnmuteTask`
    """
    __slots__ = (
        "bot",
        "remind",
        "unmute",
    )

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot: haruka.Haruka = bot
        self.remind: ReminderTask = ReminderTask(self)
        self.unmute: UnmuteTask = UnmuteTask(self)

    @property
    def conn(self) -> asyncpg.Pool:
        """The connection or connection pool to connect to the
        database.

        This is the same as the database connection of the bot.
        """
        return self.bot.conn
