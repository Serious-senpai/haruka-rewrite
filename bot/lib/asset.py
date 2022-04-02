from __future__ import annotations

import asyncio
import os
import random
import traceback
from typing import ClassVar, List, Optional, TYPE_CHECKING

import aiohttp
from yarl import URL
from bs4 import BeautifulSoup

from env import HOST
from lib import utils
if TYPE_CHECKING:
    import haruka


class AssetClient:
    """Represents a client that downloads remote resources to the
    local machine.
    """

    __slots__ = ("_ready", "bot", "anime_images_fetch", "files")
    directory: ClassVar[str] = "./bot/assets/server/images"
    if TYPE_CHECKING:
        _ready: asyncio.Event
        bot: haruka.Haruka
        anime_images_fetch: bool
        files: List[str]

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self._ready = asyncio.Event()
        self.anime_images_fetch = False

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session

    def log(self, content: str) -> None:
        self.bot.log("ASSET CLIENT: " + content)

    async def fetch_anime_images(self) -> None:
        """This function is a coroutine

        Asynchronously fetch the image TAR file from Mediafire
        and save it to the local machine.
        """
        zip_location = self.directory + "/collection.tar"

        if os.listdir(self.directory):
            return await self.__finalize()

        with utils.TimingContextManager() as measure:
            async with self.session.get("https://www.mediafire.com/file/e6vvkrzd0y0r7zd/collection.tar/file") as response:
                if response.status == 200:
                    html = await response.text(encoding="utf-8")
                    soup = BeautifulSoup(html, "html.parser")
                    download_button = soup.find("a", attrs={"class": "input popsok"})
                    file_url = download_button.get("href")

                    if not file_url:
                        return self.log(f"Cannot obtain a download URL from this element:\n{download_button}")

                else:
                    return self.log(f"Cannot fetch download URL: HTTP status {response.status}")

        self.log(f"Fetched TAR file URL in {utils.format(measure.result)}: {file_url}")

        with utils.TimingContextManager() as measure:
            async with self.session.get(file_url) as response:
                if response.status == 200:
                    with open(zip_location, "wb", buffering=0) as f:
                        try:
                            chunk_size = 4 * 2 ** 10  # 4 KB
                            while data := await response.content.read(chunk_size):
                                f.write(data)
                        except aiohttp.ClientPayloadError:
                            self.log("Exception while downloading the TAR file:\n" + traceback.format_exc() + "\nIgnoring and continuing the unzipping process.")
                else:
                    return self.log(f"Cannot fetch the TAR file from {file_url}: HTTP status {response.status}")

        size = os.path.getsize(zip_location)
        self.log(f"Downloaded TAR file in {utils.format(measure.result)}" + " (file size {:.2f} MB)".format(size / 2 ** 20))
        await self.extract_tar_file(zip_location, self.directory)
        os.remove(zip_location)
        await self.__finalize()

    async def __finalize(self) -> None:
        for filename in os.listdir(self.directory):
            path = os.path.join(self.directory, filename)
            if filename.endswith(".jfif"):
                os.rename(path, path.removesuffix(".jfif") + ".jpeg")

            await asyncio.sleep(0)

        self.files = os.listdir(self.directory)
        self._ready.set()
        self.anime_images_fetch = True

    async def extract_tar_file(self, zip_location: str, destination: str) -> None:
        args = (
            "tar",
            "-xf", zip_location,
            "-C", destination,
        )

        with utils.TimingContextManager() as measure:
            process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
            _, _stderr = await process.communicate()

        if _stderr:
            stderr = _stderr.decode("utf-8")
            self.log(f"WARNING: stderr when extracting from \"{zip_location}\" to \"{destination}\":\n" + stderr)

        self.log(f"Extracted \"{zip_location}\" to \"{destination}\" in {utils.format(measure.result)}")

    async def wait_until_ready(self) -> None:
        await self._ready.wait()

    def get_anime_image_path(self) -> Optional[str]:
        if not self.anime_images_fetch:
            return

        if self.files:
            filename = random.choice(self.files)
            return "/assets/images/" + filename

    def get_anime_image(self) -> Optional[str]:
        path = self.get_anime_image_path()
        if path:
            url = URL(HOST + path)
            return str(url)
