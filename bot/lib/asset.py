from __future__ import annotations

import asyncio
import io
import os
import random
import traceback
from typing import ClassVar, List, Optional, TYPE_CHECKING

import aiohttp
import discord
from yarl import URL
from bs4 import BeautifulSoup

from env import HOST
from lib import utils
if TYPE_CHECKING:
    import haruka


CODE_SNIPPET = """
```py
bot.loop.create_task(bot.asset_client.fetch_anime_images())
```
"""


class AssetClient:
    """Represents a client that downloads remote resources to the
    local machine.
    """

    __slots__ = ("_ready", "bot", "anime_images_fetch", "files")
    DIRECTORY: ClassVar[str] = "./bot/web/assets/images"
    if TYPE_CHECKING:
        _ready: asyncio.Event
        bot: haruka.Haruka
        files: List[str]

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self._ready = asyncio.Event()

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session

    async def fetch_anime_images(self) -> None:
        """This function is a coroutine

        Asynchronously fetch the image TAR file from Mediafire
        and save it to the local machine.
        """
        tar_location = self.DIRECTORY + "/collection.tar"

        if os.listdir(self.DIRECTORY):
            return await self.__finalize()

        with utils.TimingContextManager() as measure:
            async with self.session.get("https://www.mediafire.com/file/vjmhvpzx4brdx0v/collection.tar/file") as response:
                if response.status == 200:
                    html = await response.text(encoding="utf-8")
                    soup = BeautifulSoup(html, "html.parser")
                    download_button = soup.find("a", attrs={"class": "input popsok"})

                    if download_button is None:
                        self.bot.log("Cannot find the download button, please try again via the exec command.")
                        if self.bot.owner:
                            await self.bot.owner.send(
                                "Cannot find the download button for asset client, please try again using the following snippet:\n" + CODE_SNIPPET,
                                file=discord.File(io.StringIO(html), filename="error.html"),
                            )

                        return

                    file_url = download_button.get("href")

                    if not file_url:
                        return self.bot.log(f"Cannot obtain a download URL from this element:\n{download_button}")

                else:
                    return self.bot.log(f"Cannot fetch download URL: HTTP status {response.status}")

        self.bot.log(f"Fetched TAR file URL in {utils.format(measure.result)}: {file_url}")

        with utils.TimingContextManager() as measure:
            async with self.session.get(file_url) as response:
                if response.status == 200:
                    with open(tar_location, "wb", buffering=0) as f:
                        try:
                            while data := await response.content.read(4096):
                                f.write(data)
                        except aiohttp.ClientPayloadError:
                            self.bot.log("Exception while downloading the TAR file:\n" + traceback.format_exc() + "\nIgnoring and continuing the extracting process.")
                else:
                    return self.bot.log(f"Cannot fetch the TAR file from {file_url}: HTTP status {response.status}")

        size = os.path.getsize(tar_location)
        self.bot.log(f"Downloaded TAR file in {utils.format(measure.result)} (file size {size / 2 ** 20:.2f} MB)")
        await self.extract_tar_file(tar_location, self.DIRECTORY)
        os.remove(tar_location)
        await self.__finalize()

    async def __finalize(self) -> None:
        for filename in os.listdir(self.DIRECTORY):
            if filename.endswith(".jfif"):
                path = os.path.join(self.DIRECTORY, filename)
                os.rename(path, path.removesuffix(".jfif") + ".jpeg")

            await asyncio.sleep(0)

        self.files = os.listdir(self.DIRECTORY)
        self._ready.set()

    async def extract_tar_file(self, tar_location: str, destination: str) -> None:
        args = (
            "tar",
            "-xf", tar_location,
            "-C", destination,
        )

        with utils.TimingContextManager() as measure:
            process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
            _, _stderr = await process.communicate()

        if _stderr:
            stderr = _stderr.decode("utf-8")
            self.bot.log(f"WARNING: stderr when extracting from \"{tar_location}\" to \"{destination}\":\n" + stderr)

        self.bot.log(f"Extracted \"{tar_location}\" to \"{destination}\" in {utils.format(measure.result)}")

    async def wait_until_ready(self) -> None:
        await self._ready.wait()

    def get_anime_image_path(self) -> Optional[str]:
        if not self._ready.is_set():
            return

        if self.files:
            filename = random.choice(self.files)
            return "/assets/images/" + filename

    def get_anime_image(self) -> Optional[str]:
        path = self.get_anime_image_path()
        if path:
            url = URL(HOST + path)
            return str(url)

    def list_images(self) -> Optional[List[str]]:
        if not self._ready.is_set():
            return

        return self.files
