from __future__ import annotations

import asyncio
import imghdr
import os
import random
import traceback
from typing import ClassVar, List, Optional, Set, TYPE_CHECKING

import aiohttp
from yarl import URL
from bs4 import BeautifulSoup

import utils
from env import HOST
if TYPE_CHECKING:
    import haruka


class AssetClient:
    """Represents a client that downloads remote resources to the
    local machine.
    """

    excludes: ClassVar[Set[str]] = {
        "20210114_122632.jpg",
        "FB_IMG_1584877040826.jpg",
    }

    if TYPE_CHECKING:
        _ready: asyncio.Event
        bot: haruka.Haruka
        anime_images_fetch: bool
        files: List[str]
        session: aiohttp.ClientSession

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self.session = bot.session

        self._ready = asyncio.Event()
        self.anime_images_fetch = False

    def log(self, content: str) -> None:
        self.bot.log("ASSET CLIENT: " + content)

    async def fetch_anime_images(self) -> None:
        """This function is a coroutine

        Asynchronously fetch the image TAR file from Mediafire
        and save it to the local machine.
        """
        unzip_location = "./bot/assets/server/images"
        zip_location = unzip_location + "/collection.tar"

        if os.listdir(unzip_location):
            return await self._finalize()

        with utils.TimingContextManager() as measure:
            async with self.session.get("https://www.mediafire.com/file/uw42hxy45psweoa/Collection.tar/file") as response:
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
        await self.extract_tar_file(zip_location, unzip_location)
        os.remove(zip_location)
        await self._finalize()

    async def _finalize(self) -> None:
        self.files = await asyncio.to_thread(self._filter_image_files)
        self._ready.set()
        self.anime_images_fetch = True

    def _filter_image_files(self) -> List[str]:
        _files = set(os.listdir("./bot/assets/server/images"))
        _files -= self.excludes
        _to_remove = set()
        for file in _files:
            if imghdr.what(f"./bot/assets/server/images/{file}") is None:
                _to_remove.add(file)

        _files -= _to_remove
        return list(_files)

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
