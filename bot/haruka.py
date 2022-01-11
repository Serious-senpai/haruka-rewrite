import asyncio
import contextlib
import datetime
import io
import os
import signal
import sys
import traceback
from typing import Any, Deque, Dict, List, Optional

import aiohttp
import asyncpg
import discord
import topgg
import youtube_dl
from discord.ext import commands, tasks
from discord.utils import escape_markdown as escape

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

    def __init__(self, *args, **kwargs) -> None:
        self.logfile: io.TextIOWrapper = open("./log.txt", "a", encoding="utf-8")
        self.owner: Optional[discord.User] = None
        self._clear_counter()
        self._load_env()
        signal.signal(signal.SIGTERM, self.kill)

        super().__init__(*args, **kwargs)

    def _load_env(self) -> None:
        """Load the environment variables"""
        self.TOKEN: str = os.environ["TOKEN"]
        self.DATABASE_URL: str = os.environ["DATABASE_URL"]
        self.HOST: str = os.environ.get("HOST", "https://haruka39.herokuapp.com/").strip("/")
        self.TOPGG_TOKEN: Optional[str] = os.environ.get("TOPGG_TOKEN")

    def _clear_counter(self) -> None:
        """Clear the text command and slash command counter"""
        self._command_count: Dict[str, List[commands.Context]] = {}
        self._slash_command_count: Dict[str, List[discord.Interaction]] = {}
        super()._clear_counter()

    async def start(self) -> None:
        asyncio.current_task().set_name("MainTask")

        # Prepare database connection
        await self.prepare_database()

        # Create side session
        user_agent: str = youtube_dl.utils.random_user_agent()
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(headers={"User-Agent": user_agent})
        self.log(f"Created side session, using User-Agent: {user_agent}")

        # Start the bot
        self.loop.create_task(self.startup())
        self.uptime: datetime.datetime = datetime.datetime.now()
        await super().start(self.TOKEN)

    async def prepare_database(self) -> None:
        self.conn: asyncpg.Pool = await asyncpg.create_pool(
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
            CREATE TABLE IF NOT EXISTS rpg (id text, description text, world int, location int, type int, level int, xp int, money int, items text, hp int, travel timestamptz, state text);
        """)

        for extension in ("pg_trgm",):
            with contextlib.suppress(asyncpg.DuplicateObjectError):
                await self.conn.execute(f"CREATE EXTENSION {extension};")

        self.log("Successfully initialized database.")

    def log(self, content: Any) -> None:
        content: str = str(content).replace("\n", "\nHARUKA | ")
        self.logfile.write(f"HARUKA | {content}\n")
        self.logfile.flush()

    async def _change_activity_after_booting(self) -> None:
        await asyncio.sleep(20.0)
        await self.change_presence(activity=discord.Game("@Haruka help"))

    async def startup(self) -> None:
        await self.wait_until_ready()
        self.loop.create_task(self._change_activity_after_booting())
        await self.__do_startup()

    async def __do_startup(self) -> None:
        import image
        import game
        import task
        import tests
        from game.core import PT

        # Get bot owner
        app_info: discord.AppInfo = await self.application_info()
        if app_info.team:
            self.owner_id: int = app_info.team.owner_id
        else:
            self.owner_id: int = app_info.owner.id

        self.owner = await self.fetch_user(self.owner_id)

        # Overwrite slash commands
        await self.overwrite_slash_commands()

        # Prepare player cache
        self.players: game.PlayerCache = game.PlayerCache()
        self._connection.players = self.players

        # Schedule all on_arrival tasks for RPG players
        rows: List[asyncpg.Record] = await self.conn.fetch("SELECT * FROM rpg;")
        user: discord.User
        player: PT
        for row in rows:
            user = await self.fetch_user(row["id"])  # Union[str, int]
            player = await game.BasePlayer.from_user(user)
            self.loop.create_task(player.location.on_arrival(player))
            player.release()
            await asyncio.sleep(0.1)

        # Load bot helpers
        self.image: image.ImageClient = image.ImageClient(
            self,
            image.WaifuPics,
            image.WaifuIm,
            image.NekosLife,
            image.Asuna,
        )
        self.task: task.TaskManager = task.TaskManager(self)
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
            self.topgg: topgg.DBLClient = topgg.DBLClient(
                self,
                self.TOPGG_TOKEN,
                autopost=True,
                autopost_interval=900,
                session=self.session,
            )

        # Fetch repository's latest commits
        async with self.session.get("https://api.github.com/repos/Saratoga-CV6/haruka-rewrite/commits") as response:
            if response.ok:
                json: Dict[str, Any] = await response.json()
                desc: List[str] = []

                for commit in json[:4]:
                    sha: str = commit["sha"][:6]
                    message: str = commit["commit"]["message"].split("\n")[0]
                    url: str = commit["html_url"]
                    desc.append(f"__[`{sha}`]({url})__ {escape(message)}")

                self.latest_commits: str = "\n".join(desc)
                self.log("Fetched latest repository commits")

            else:
                self.log(f"Warning: Unable to fetch repository's commits (status {response.status})")
                self.latest_commits: str = "*No data*"

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
        await self.owner.send(
            message,
            embed=self.display_status if send_state else None,
            file=discord.File("./log.txt") if send_log else None,
        )

    @property
    def display_status(self) -> discord.Embed:
        guilds: List[discord.Guild] = self.guilds
        users: List[discord.User] = self.users
        emojis: List[discord.Emoji] = self.emojis
        stickers: List[discord.Sticker] = self.stickers
        voice_clients: List[discord.VoiceProtocol] = self.voice_clients
        private_channels: List[discord.abc.PrivateChannel] = self.private_channels
        messages: Deque[discord.Message] = self._connection._messages

        desc: str = "**Commands usage:** " + escape(", ".join(f"{command}: {len(uses)}" for command, uses in self._command_count.items())) + "\n**Slash commands usage:** " + escape(", ".join(f"{command}: {len(uses)}" for command, uses in self._slash_command_count.items()))

        em: discord.Embed = discord.Embed(
            title="Internal status",
            description=desc,
        )
        em.set_thumbnail(url=self.user.avatar.url)

        em.add_field(
            name="Cached servers",
            value=f"{len(guilds)} servers",
            inline=False,
        )
        em.add_field(
            name="Cached users",
            value=f"{len(users)} users",
        )
        em.add_field(
            name="Cached emojis",
            value=f"{len(emojis)} emojis",
        )
        em.add_field(
            name="Cached stickers",
            value=f"{len(stickers)} stickers",
        )
        em.add_field(
            name="Cached voice clients",
            value=f"{len(voice_clients)} voice clients",
        )
        em.add_field(
            name="Cached DM channels",
            value=f"{len(private_channels)} channels",
        )
        em.add_field(
            name="Cached messages",
            value=f"{len(messages)} messages",
            inline=False,
        )
        em.add_field(
            name="Uptime",
            value=datetime.datetime.now() - self.uptime,
            inline=False,
        )

        return em

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
