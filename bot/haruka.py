import asyncio
import datetime
import os
import signal
import sys
import traceback
from typing import Any, Deque, Dict, List, Optional

import aiohttp
import discord
import topgg
from discord.ext import commands, tasks
from discord.utils import escape_markdown as escape

from slash import SlashMixin


class Haruka(SlashMixin, commands.Bot):

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
        # Initial state
        self.owner: Optional[discord.User] = None
        self.clear_counter()
        self._load_env()

        super().__init__(*args, **kwargs)

    def _load_env(self) -> None:
        self.TOKEN: str = os.environ["TOKEN"]
        self.HOST: str = os.environ.get("HOST", "https://haruka39.herokuapp.com/").strip("/")
        self.DATABASE_URL: str = os.environ["DATABASE_URL"]
        self.TOPGG_TOKEN: Optional[str] = os.environ.get("TOPGG_TOKEN")

    def clear_counter(self) -> None:
        self._command_count: Dict[str, List[commands.Context]] = {}
        self._slash_command_count: Dict[str, List[discord.Interaction]] = {}

    async def start(self) -> None:
        # Handle SIGTERM signal from Heroku
        signal.signal(signal.SIGTERM, self.kill)

        # Setup logging file
        self.logfile = open("./log.txt", "a", encoding="utf-8")

        # Connect to database
        import database

        async with database.Database(self, self.DATABASE_URL) as self.conn:
            # Initialize state
            asyncio.current_task().set_name("Haruka main task")
            self.session: aiohttp.ClientSession = aiohttp.ClientSession()
            self.loop.create_task(self.startup())
            self.uptime: datetime.datetime = datetime.datetime.now()

            # Start the bot
            await super().start(self.TOKEN)

    def _get_external_source(self) -> None:
        import image
        import task

        self.image: image.ImageClient = image.ImageClient(
            self,
            image.WaifuPics,
            image.WaifuIm,
            image.NekosLife,
            image.Asuna,
        )
        self.task: task.TaskManager = task.TaskManager(self)
        self.log("Loaded all external sources.")

    def log(self, content: Any) -> None:
        content: str = str(content).replace("\n", "\nHARUKA | ")
        self.logfile.write(f"HARUKA | {content}\n")

    async def startup(self) -> None:
        # Get bot owner
        await self.wait_until_ready()
        app_info: discord.AppInfo = await self.application_info()
        if app_info.team:
            self.owner_id: int = app_info.team.owner_id
        else:
            self.owner_id: int = app_info.owner.id

        self.owner = await self.fetch_user(self.owner_id)

        # Run youtube-dl tests
        tasks: List[asyncio.Task] = []

        for url in (
            "https://www.youtube.com/watch?v=Hy9s13hWsoc",
            "https://www.youtube.com/watch?v=n89SKAymNfA",
        ):
            task: asyncio.Task = self.loop.create_task(self._ytdl_test(url))
            tasks.append(task)

        self._get_external_source()
        self.loop.create_task(self.overwrite_slash_commands())  # Ignore exceptions

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

                for commit in json[:3]:
                    message: str = commit["commit"]["message"].split("\n")[0]
                    url: str = commit["html_url"]
                    desc.append(f"__[{message}]({url})__")

                self.latest_commits: str = "\n".join(content for content in desc)
                self.log("Fetched latest repository commits")

            else:
                self.log(f"Warning: Unable to fetch repository's commits (status {response.status})")
                self.latest_commits: str = "*No data*"

        await asyncio.gather(*tasks)
        self.log(f"Finished {len(tasks)} youtube-dl tests.")

        try:
            await self.report("Haruka is ready!", send_state=False)
        except BaseException:
            self.log("Cannot send ready notification:")
            self.log(traceback.format_exc())

    async def _ytdl_test(self, url: str) -> None:
        args: List[str] = [
            "--get-url",
            "--extract-audio",
            "--audio-format", "opus",
            "--rm-cache-dir",
            "--force-ipv4",
            url,
        ]

        args.insert(0, "youtube-dl")
        process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        output, _ = await process.communicate()

        content: str = output.decode("utf-8")
        self.log(f"Finished ytdl test for {url}:\nOutput: {content}")

    def kill(self, *args) -> None:
        print("Received SIGTERM signal. Terminating bot...")
        self.log("Received SIGTERM signal. Terminating bot...")
        self.loop.create_task(self.close())

    async def close(self) -> None:
        await self.conn.close()
        await self.session.close()
        try:
            await self.report("Terminating bot. This is the final report.")
            print("Final report has been sent.")
        except BaseException:
            print("Unable to send log file during termination.")
            traceback.print_exc()
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
        self.logfile.flush()
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
            color=0x2ECC71,
            timestamp=discord.utils.utcnow(),
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
        asyncio.current_task().set_name("Keep server alive")
        async with self.session.get(self.HOST) as response:
            if not response.status == 200:
                self.log(f"Warning: _keep_alive task returned response code {response.status}")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        self.log(f"Exception in {event_method}:")
        self.log(traceback.format_exc())
        await self.report("An error has just occurred and was handled by `on_error`", send_state=False)
