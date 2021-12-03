import asyncio
import datetime
import os
import signal
import traceback
from typing import Any, Callable, Coroutine, Deque, Dict, List, Optional, OrderedDict

import aiohttp
import discord
import topgg
from discord.ext import commands, tasks

import database


class Haruka(commands.Bot):
    TOKEN: str = os.environ["TOKEN"]
    HOST: Optional[str] = os.environ.get("HOST")
    TOPGG_TOKEN: Optional[str] = os.environ.get("TOPGG_TOKEN")
    DATABASE_URL: str = os.environ["DATABASE_URL"]

    BASE_URL: str = "https://discord.com/api/v8"
    headers: Dict[str, str] = {
        "Authorization": f"Bot {TOKEN}",
    }
    slash_commands: Dict[str, Callable[[discord.Interaction], Coroutine[Any, Any, Any]]] = {}
    json: List[Dict[str, Any]] = []

    def register_slash_command(self, coro: Callable[[discord.Interaction], Coroutine[Any, Any, Any]], json: Dict[str, Any]) -> None:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("Slash commands must be coroutine.")

        self.slash_commands[json["name"]] = coro
        self.json.append(json)

    def slash(self, json) -> Callable[[Callable[[discord.Interaction], Coroutine[Any, Any, Any]]], None]:
        def decorator(coro: Callable[[discord.Interaction], Coroutine[Any, Any, Any]]) -> None:
            return self.register_slash_command(coro, json)
        return decorator

    async def overwrite_slash_commands(self) -> None:
        # Wait until ready so that the "user" attribute is available
        await self.wait_until_ready()

        # Now register all slash commands
        self.log("Overwriting slash commands: " + ", ".join(json["name"] for json in self.json))
        async with self.session.put(
            f"{self.BASE_URL}/applications/{self.user.id}/commands",
            json=self.json,
            headers=self.headers,
        ) as response:
            self.log(f"Slash commands setup returned status code {response.status}.")
            if not response.ok:
                print(f"Warning: Slash commands setup returned status code {response.status}.")
                json = await response.json()
                self.log(f"JSON type: {json.__class__.__name__}")
                self.log(json)

    async def process_slash_commands(self, interaction: discord.Interaction) -> None:
        name: str = interaction.data["name"]

        # Count slash commands
        if not await self.is_owner(interaction.user):
            if name not in self._slash_command_count:
                self._slash_command_count[name] = 0

            self._slash_command_count[name] += 1

        # Process command
        await self.slash_commands[name](interaction)

    async def start(self) -> None:
        # Handle SIGTERM signal from Heroku
        signal.signal(signal.SIGTERM, self.kill)

        # Setup logging file
        self.logfile = open("./log.txt", "a", encoding="utf-8")

        # Connect to database
        async with database.Database(self, self.DATABASE_URL) as self.conn:
            # Create side session for other stuff
            async with aiohttp.ClientSession() as self.session:
                # Initialize state
                self.loop.create_task(self.startup())

                self.uptime: datetime.datetime = datetime.datetime.now()
                self._command_count: Dict[str, int] = {}
                self._slash_command_count: Dict[str, int] = {}
                self.owner: Optional[discord.User] = None
                self.host: Optional[str] = self.HOST.strip("/") if self.HOST else None
                self._cancelling_signal: asyncio.Event = asyncio.Event()

                # Start the bot
                await asyncio.wait([super().start(self.TOKEN), self.close()], return_when=asyncio.FIRST_COMPLETED)

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

    def log(self, log: Any) -> None:
        content: str = str(log).replace("\n", "\nHARUKA | ")
        self.logfile.write(f"HARUKA | {content}\n")
        self.logfile.flush()

    async def startup(self) -> None:
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
        if self.host:
            try:
                self._keep_alive.start()
            except Exception as ex:
                self.log(f"An exception occured when starting _keep_alive: {ex}")
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

        await asyncio.gather(*tasks)
        self.log(f"Finished {len(tasks)} youtube-dl tests.")

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

        # Wait for the bot cache to ready
        await self.wait_until_ready()

        # Get bot owner
        app_info: discord.AppInfo = await self.application_info()
        if app_info.team:
            self.owner_id: int = app_info.team.owner_id
        else:
            self.owner_id: int = app_info.owner.id

        self.owner: discord.User = await self.fetch_user(self.owner_id)

        try:
            await self.report("Haruka is ready!", send_state=False)
        except Exception as ex:
            self.log(f"Cannot send ready notification: {ex}")

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

        try:
            content: str = output.decode("utf-8")
        except BaseException:
            self.log("Cannot decode output for ytdl test.")
            self.log(traceback.format_exc())
            self.log(f"Finished ytdl test on {url}:\nOutput: {output}")
        else:
            self.log(f"Finished ytdl test on {url}:\nOutput: {content}")

    def kill(self, *args) -> None:
        self.log("Received SIGTERM signal. Terminating bot...")
        self._cancelling_signal.set()

    async def close(self) -> None:
        await self._cancelling_signal.wait()
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
        print("Writing log file to the console:")
        print("-------------------------------------------")
        with open("./log.txt", "r") as f:
            print(f.read())

    async def report(self, message: str, *, send_state: bool = True, file: discord.File = None) -> None:
        files: List[discord.File] = [discord.File("./log.txt")]
        if file:
            files.append(file)

        await self.owner.send(
            message,
            embed=self.display_status if send_state else None,
            files=files,
        )

    @property
    def display_status(self) -> discord.Embed:
        guilds: Dict[int, discord.Guild] = self._connection._guilds
        users: Dict[int, discord.User] = self._connection._users
        emojis: Dict[int, discord.Emoji] = self._connection._emojis
        stickers: Dict[int, discord.GuildSticker] = self._connection._stickers
        voice_clients: Dict[int, discord.VoiceProtocol] = self._connection._voice_clients
        private_channels: OrderedDict[int, discord.PrivateChannel] = self._connection._private_channels
        messages: Deque[discord.Message] = self._connection._messages

        em: discord.Embed = discord.Embed(
            title="Internal status",
            description="**Commands usage:** " + ", ".join(f"{command}: {uses}" for command, uses in self._command_count.items())
            + "\n**Slash commands usage:** " + ", ".join(f"{command}: {uses}" for command, uses in self._slash_command_count.items()),
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

    @tasks.loop(
        minutes=10,
    )
    async def _keep_alive(self) -> None:
        async with self.session.get(self.host) as response:
            if not response.status == 200:
                self.log(f"Warning: _keep_alive task returned response code {response.status}")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        self.log(f"Exception in {event_method}:")
        self.log(traceback.format_exc())
        await self.report("An error has just occurred and was handled by `on_error`", send_state=False)
