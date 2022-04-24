from __future__ import annotations

import asyncio
import contextlib
import datetime
import io
import signal
import sys
import traceback
from typing import Any, Callable, Coroutine, Deque, Dict, List, Optional, Union, TYPE_CHECKING

import aiohttp
import asyncpg
import discord
import topgg
import youtube_dl
from aiohttp import web
from discord import app_commands
from discord.ext import commands, tasks
from discord.state import ConnectionState
from discord.utils import MISSING, escape_markdown as escape

import env
import side
import web as server
from _types import Context, Interaction, Loop
from lib import asset, tests
from lib.audio import AudioClient
from lib.image import ImageClient


if TYPE_CHECKING:
    from discord.app_commands.commands import Command, CommandCallback, Group, P, T

    class _ConnectionState(ConnectionState):
        conn: asyncpg.Pool
        _messages: Deque[discord.Message]


class Haruka(commands.Bot):

    if TYPE_CHECKING:
        _command_count: Dict[str, List[Context]]
        _slash_command_count: Dict[str, List[Interaction]]
        _connection: _ConnectionState
        _eval_task: Optional[asyncio.Task]
        _create_image_slash_command: Coroutine[Any, Any, None]

        app: server.WebApp
        asset_client: asset.AssetClient
        audio: AudioClient
        conn: asyncpg.Pool
        image: ImageClient
        logfile: io.TextIOWrapper
        loop: Loop
        owner: Optional[discord.User]
        owner_bypass: bool
        runner: web.AppRunner
        session: aiohttp.ClientSession
        side_client: Optional[side.SideClient]
        uptime: datetime.datetime

    def __init__(self, *args, **kwargs) -> None:
        signal.signal(signal.SIGTERM, self.kill)

        super().__init__(*args, **kwargs)
        self.logfile = open("./bot/assets/server/log.txt", "a", encoding="utf-8")
        self.owner = None
        self._clear_counter()

        if env.SECONDARY_TOKEN:
            print("SECONDARY_TOKEN detected, initializing SideClient.")
            self.side_client = side.SideClient(self, env.SECONDARY_TOKEN)
        else:
            self.side_client = None

        self.__initialize_clients()

    def __initialize_clients(self) -> None:
        self.asset_client = asset.AssetClient(self)
        self.image = ImageClient(self)
        self.audio = AudioClient(self)

    def _clear_counter(self) -> None:
        """Clear the text command and slash command counter"""
        self._command_count = {}
        self._slash_command_count = {}

    async def setup_hook(self) -> None:
        # Prepare database connection
        await self.prepare_database()

        # Create side session
        headers = {
            "User-Agent": youtube_dl.utils.random_user_agent(),
        }
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(connect=5.0),
        )
        self.log("Created side session")

        # Initialize Top.gg client
        if env.TOPGG_TOKEN:
            self.topgg = topgg.DBLClient(
                self,
                env.TOPGG_TOKEN,
                autopost=True,
                autopost_interval=900,
                session=self.session,
            )

        # Prepare image client
        await self.image.prepare()
        self.log("Loaded image client")

        # Start server asynchronously
        self.app = server.WebApp(self)
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        port = int(env.PORT)
        site = web.TCPSite(self.runner, None, port)
        await site.start()
        print(f"Started serving on port {port}")

        self.uptime = discord.utils.utcnow()

        if self.side_client:
            self.loop.create_task(self.side_client.start())

        self.loop.create_task(self.startup())

    async def prepare_database(self) -> None:
        self.conn = await asyncpg.create_pool(
            env.DATABASE_URL,
            min_size=2,
            max_size=10,
            max_inactive_connection_lifetime=3.0,
        )
        self._connection.conn = self.conn
        self.log("Created connection pool")

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prefix (id text, pref text);
            CREATE TABLE IF NOT EXISTS youtube (id text, queue text[]);
            CREATE TABLE IF NOT EXISTS blacklist (id text);
            CREATE TABLE IF NOT EXISTS remind (id text, time timestamptz, content text, url text, original timestamptz);
            CREATE TABLE IF NOT EXISTS inactivity (id text primary key, time timestamptz);
        """)

        self.log("Successfully initialized database.")

    def log(self, content: Any) -> None:
        content = str(content).replace("\n", "\nHARUKA: ")
        self.logfile.write(f"HARUKA: {content}\n")
        self.logfile.flush()

    async def reset_inactivity_counter(self, guild_id: Union[int, str]) -> None:
        now = discord.utils.utcnow()
        guild_id = str(guild_id)
        await self.conn.execute(
            """
            INSERT INTO inactivity
            VALUES ($1, $2)
            ON CONFLICT (id) DO UPDATE
                SET time = excluded.time;
            """,
            guild_id,
            now,
        )
        self.log(f"Reset inactivity counter for guild ID {guild_id} to {now}")
        self.guild_leaver.restart()

    async def _change_activity_after_booting(self) -> None:
        await asyncio.sleep(20.0)
        await self.change_presence(activity=discord.Game("@Haruka help"))

    async def startup(self) -> None:
        await self.wait_until_ready()
        self.loop.create_task(self._change_activity_after_booting(), name="Change activity")
        await self.__do_startup()

    async def __do_startup(self) -> None:
        # Start tests
        test_running_task = self.loop.create_task(tests.run_all_tests(self), name="Startup tests")

        # Fetch anime images
        image_fetching_task = self.loop.create_task(self.asset_client.fetch_anime_images(), name="Startup image fetching")

        # Create the /image command
        create_image_slash_command = self.loop.create_task(self._create_image_slash_command)

        # Get bot owner
        app_info = await self.application_info()
        if app_info.team:
            self.owner_id = app_info.team.owner_id
        else:
            self.owner_id = app_info.owner.id
        self.owner = await self.fetch_user(self.owner_id)

        # Initialize guild activity check
        now = discord.utils.utcnow()
        for guild in self.guilds:
            row = await self.conn.fetchrow(f"SELECT * FROM inactivity WHERE id = '{guild.id}';")
            if not row:
                await self.conn.execute(f"INSERT INTO inactivity VALUES ('{guild.id}', $1);", now)
                self.log(f"Inserted guild ID {guild.id} into the inactivity table: {now}")

        self.log("Initialized all guild inactivity checks")

        # Start all future tasks
        for task in (self._keep_alive, self.reminder, self.guild_leaver):
            try:
                task.start()
            except BaseException:
                self.log(f"An exception occured when starting {task.coro.__name__}:")
                self.log(traceback.format_exc())
            else:
                self.log(f"Started {task.coro.__name__}")

        # Fetch repository's latest commits
        async with self.session.get("https://api.github.com/repos/Serious-senpai/haruka-rewrite/commits") as response:
            if response.ok:
                js = await response.json(encoding="utf-8")
                desc = []

                for commit in js[:4]:
                    sha = commit["sha"][:6]
                    message = commit["commit"]["message"].split("\n")[0]
                    url = commit["html_url"]
                    desc.append(f"__[`{sha}`]({url})__ {escape(message)}")

                self.latest_commits = "\n".join(desc).replace(r"\`\`", "`")
                self.log("Fetched latest repository commits")

            else:
                self.log(f"WARNING: Unable to fetch repository's commits (status {response.status})")
                self.latest_commits = "*No data*"

        # Complete tasks
        await test_running_task
        await create_image_slash_command
        await image_fetching_task

        try:
            await self.report("Haruka is ready!", send_state=False)
        except BaseException:
            self.log("Cannot send ready notification:")
            self.log(traceback.format_exc())

    def slash(
        self,
        *,
        name: str,
        description: str,
        guilds: List[discord.Object] = MISSING,
        verified_client: bool = True,
        unverified_client: bool = True,
    ) -> Callable[[CommandCallback[Group, P, T]], Command[Group, P, T]]:
        def decorator(func: CommandCallback[Group, P, T]) -> Command[Group, P, T]:
            command = app_commands.Command(name=name, description=description, callback=func)
            if verified_client:
                if self.side_client:
                    self.side_client.tree.add_command(command, guilds=guilds)
                else:
                    self.log("A secondary token should be provided to register command to a verified client")

            if unverified_client:
                self.tree.add_command(command, guilds=guilds)

        return decorator

    def kill(self, *args) -> None:
        print("Received SIGTERM signal. Terminating bot...")
        self.log("Received SIGTERM signal. Terminating bot...")
        self.loop.create_task(self.close())

    async def close(self) -> None:
        await self.runner.cleanup()
        self.log("Closed server.")
        await self.conn.close()
        self.log("Closed database connection pool for bot.")
        await self.session.close()
        self.log("Closed side session.")
        try:
            await self.report("Terminating bot. This is the final report.")
            print("Final report has been sent.")
        finally:
            await super().close()
            print("Writing log file to the console:\n")
            with open("./bot/assets/server/log.txt", "r", encoding="utf-8") as f:
                print(f.read())

    async def report(
        self,
        message: str,
        *,
        send_state: bool = True,
        send_log: bool = True,
    ) -> None:
        if self.owner is not None:
            await self.owner.send(
                message,
                embed=self.display_status if send_state else None,  # type: ignore
                file=discord.File("./bot/assets/server/log.txt") if send_log else None,  # type: ignore
            )

    @property
    def display_status(self) -> discord.Embed:
        guilds = self.guilds
        users = self.users
        emojis = self.emojis
        stickers = self.stickers
        voice_clients = self.voice_clients
        private_channels = self.private_channels
        messages = self._connection._messages

        desc = "**Commands usage:** " + escape(", ".join(f"{command}: {len(uses)}" for command, uses in self._command_count.items())) + "\n**Slash commands usage:** " + escape(", ".join(f"{command}: {len(uses)}" for command, uses in self._slash_command_count.items()))

        embed = discord.Embed(description=desc)
        embed.set_thumbnail(url=self.user.avatar.url)
        embed.set_author(
            name="Internal status",
            icon_url=self.user.avatar.url,
        )

        embed.add_field(
            name="Cached servers",
            value=f"{len(guilds)} servers",
            inline=False,
        )
        embed.add_field(
            name="Cached users",
            value=f"{len(users)} users",
        )
        embed.add_field(
            name="Cached emojis",
            value=f"{len(emojis)} emojis",
        )
        embed.add_field(
            name="Cached stickers",
            value=f"{len(stickers)} stickers",
        )
        embed.add_field(
            name="Cached voice clients",
            value=f"{len(voice_clients)} voice clients",
        )
        embed.add_field(
            name="Cached DM channels",
            value=f"{len(private_channels)} channels",
        )
        embed.add_field(
            name="Cached messages",
            value=f"{len(messages)} messages",
            inline=False,
        )
        embed.add_field(
            name="Uptime",
            value=discord.utils.utcnow() - self.uptime,
            inline=False,
        )

        return embed

    @tasks.loop(minutes=5)
    async def _keep_alive(self) -> None:
        asyncio.current_task().set_name("KeepServerAlive")  # type: ignore
        async with self.session.get(env.HOST) as response:
            if not response.status == 200:
                self.log(f"WARNING: _keep_alive task returned response code {response.status}")

    @tasks.loop()
    async def reminder(self) -> None:
        row = await self.conn.fetchrow("SELECT * FROM remind ORDER BY time;")
        if not row:
            await asyncio.sleep(3600)
            return

        await discord.utils.sleep_until(row["time"])
        await self.conn.execute(
            "DELETE FROM remind WHERE id = $1 AND time = $2 AND original = $3;",
            row["id"], row["time"], row["original"],
        )

        try:
            user = await self.fetch_user(row["id"])  # Union[str, int]
        except BaseException:
            return

        embed = discord.Embed(
            description=row["content"],
            timestamp=row["original"],
        )
        embed.set_author(
            name=f"{user.name}, this is your reminder.",
            icon_url=self.user.avatar.url,
        )
        embed.add_field(
            name="Original message URL",
            value=row["url"],
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)

        with contextlib.suppress(discord.Forbidden):
            await user.send(embed=embed)

    @tasks.loop()
    async def guild_leaver(self) -> None:
        row = await self.conn.fetchrow("SELECT * FROM inactivity ORDER BY time;")
        if not row:
            await asyncio.sleep(3600)
            return

        await discord.utils.sleep_until(row["time"] + datetime.timedelta(days=30))
        guild_id = row["id"]
        await self.conn.execute("DELETE FROM inactivity WHERE id = $1", guild_id)

        guild = self.get_guild(int(guild_id))
        if guild:
            with contextlib.suppress(discord.HTTPException):
                await guild.leave()
                await asyncio.sleep(3.0)
