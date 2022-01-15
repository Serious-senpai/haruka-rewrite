import asyncio
import contextlib
import io
import os
import signal
import sys
import traceback
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

import aiohttp
import asyncpg
import discord
import topgg
import youtube_dl
from aiohttp import web
from discord.ext import commands, tasks
from discord.utils import escape_markdown as escape

import image
import server
import task
from slash import SlashMixin


class Haruka(commands.Bot, SlashMixin):

    if sys.platform == "win32":
        loop: asyncio.ProactorEventLoop
    else:
        try:
            import uvloop
        except ImportError:
            loop: asyncio.SelectorEventLoop
        else:
            loop: uvloop.Loop

    if TYPE_CHECKING:
        TOKEN: str
        DATABASE_URL: str
        HOST: str
        TOPGG_TOKEN: Optional[str]
        logfile: io.TextIOWrapper
        owner: Optional[discord.User]
        _command_count: Dict[str, List[commands.Context]]
        _slash_command_count: Dict[str, List[discord.Interaction]]

    def __init__(self, *args, **kwargs) -> None:
        self.TOKEN = os.environ["TOKEN"]
        self.DATABASE_URL = os.environ["DATABASE_URL"]
        self.HOST = os.environ.get("HOST", "https://haruka39.herokuapp.com/").strip("/")
        self.TOPGG_TOKEN = os.environ.get("TOPGG_TOKEN")

        self.logfile = open("./log.txt", "a", encoding="utf-8")
        self.owner = None
        self._clear_counter()
        signal.signal(signal.SIGTERM, self.kill)

        super().__init__(*args, **kwargs)

    def _clear_counter(self) -> None:
        """Clear the text command and slash command counter"""
        self._command_count = {}
        self._slash_command_count = {}

    async def start(self) -> None:
        asyncio.current_task().set_name("MainTask")

        # Prepare database connection
        await self.prepare_database()

        # Create side session
        user_agent = youtube_dl.utils.random_user_agent()
        self.session = aiohttp.ClientSession(headers={"User-Agent": user_agent})
        self.log(f"Created side session, using User-Agent: {user_agent}")

        # Start server asynchronously
        app = server.WebApp(bot=self)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(self.runner, None, port)
        await site.start()
        print(f"Started serving on port {port}")

        # Start the bot
        self.loop.create_task(self.startup())
        self.uptime = discord.utils.utcnow()
        await super().start(self.TOKEN)

    async def prepare_database(self) -> None:
        self.conn = await asyncpg.create_pool(
            self.DATABASE_URL,
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
            CREATE TABLE IF NOT EXISTS inactivity (id text, time timestamptz);
        """)

        for extension in ("pg_trgm",):
            with contextlib.suppress(asyncpg.DuplicateObjectError):
                await self.conn.execute(f"CREATE EXTENSION {extension};")

        self.log("Successfully initialized database.")

    def log(self, content: Any) -> None:
        content = str(content).replace("\n", "\nHARUKA | ")
        self.logfile.write(f"HARUKA | {content}\n")
        self.logfile.flush()

    async def reset_inactivity_counter(self, guild_id: Union[int, str]) -> None:
        await self.conn.execute(f"UPDATE inactivity SET time = $1 WHERE id = '{guild_id}';", discord.utils.utcnow())
        self.task.leave.restart()

    async def _change_activity_after_booting(self) -> None:
        await asyncio.sleep(20.0)
        await self.change_presence(activity=discord.Game("@Haruka help"))

    async def startup(self) -> None:
        await self.wait_until_ready()
        self.loop.create_task(self._change_activity_after_booting())
        await self.__do_startup()

    async def __do_startup(self) -> None:
        import tests

        # Get bot owner
        app_info = await self.application_info()
        if app_info.team:
            self.owner_id = app_info.team.owner_id
        else:
            self.owner_id = app_info.owner.id
        self.owner = await self.fetch_user(self.owner_id)

        # Overwrite slash commands
        await self.overwrite_slash_commands()

        # Initialize guild activity check
        now = discord.utils.utcnow()
        for guild in self.guilds:
            row = await self.conn.fetchrow(f"SELECT * FROM inactivity WHERE id = '{guild.id}';")
            if not row:
                await self.conn.execute(f"INSERT INTO inactivity VALUES ('{guild.id}', $1);", now)
        self.log("Initialized all guild inactivity checks")

        # Load bot helpers
        self.image = image.ImageClient(
            self,
            image.WaifuPics,
            image.WaifuIm,
            image.NekosLife,
            image.Asuna,
        )
        self.task = task.TaskManager(self)
        self._connection.task = self.task
        self.log("Loaded all bot helpers.")

        # Keep the server alive
        try:
            self._keep_alive.start()
        except BaseException:
            self.log("An exception occured when starting _keep_alive:")
            self.log(traceback.format_exc())
        else:
            self.log("Started _keep_alive task")

        # Post server count every 15 minutes
        if self.TOPGG_TOKEN:
            self.topgg = topgg.DBLClient(
                self,
                self.TOPGG_TOKEN,
                autopost=True,
                autopost_interval=900,
                session=self.session,
            )

        # Fetch repository's latest commits
        async with self.session.get("https://api.github.com/repos/Saratoga-CV6/haruka-rewrite/commits") as response:
            if response.ok:
                js = await response.json()
                desc = []

                for commit in js[:4]:
                    sha = commit["sha"][:6]
                    message = commit["commit"]["message"].split("\n")[0]
                    url = commit["html_url"]
                    desc.append(f"__[`{sha}`]({url})__ {escape(message)}")

                self.latest_commits = "\n".join(desc)
                self.log("Fetched latest repository commits")

            else:
                self.log(f"Warning: Unable to fetch repository's commits (status {response.status})")
                self.latest_commits = "*No data*"

        # Run tests
        await tests.run_all_tests(log=self.log)

        try:
            await self.report("Haruka is ready!", send_state=False)
        except BaseException:
            self.log("Cannot send ready notification:")
            self.log(traceback.format_exc())

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

    def cleanup(self) -> None:
        super().cleanup()
        print("Writing log file to the console:\n")
        with open("./log.txt", "r", encoding="utf-8") as f:
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
                embed=self.display_status if send_state else None,
                file=discord.File("./log.txt") if send_log else None,
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

        embed = discord.Embed(
            title="Internal status",
            description=desc,
        )
        embed.set_thumbnail(url=self.user.avatar.url)

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

    @tasks.loop(minutes=10)
    async def _keep_alive(self) -> None:
        asyncio.current_task().set_name("KeepServerAlive")
        async with self.session.get(self.HOST) as response:
            if not response.status == 200:
                self.log(f"Warning: _keep_alive task returned response code {response.status}")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        self.log(f"Exception in {event_method}:")
        self.log(traceback.format_exc())
        await self.report("An error has just occurred and was handled by `on_error`", send_state=False)
