from __future__ import annotations

import asyncio
import contextlib
import functools
import os
import random
import traceback
from typing import List, Optional, TYPE_CHECKING

import aiohttp
from yarl import URL
from bs4 import BeautifulSoup

import env
import utils
if TYPE_CHECKING:
    import haruka


if not os.path.isdir("./bot/assets/server/images"):
    os.mkdir("./bot/assets/server/images")


class AssetClient:
    """Represents a client that downloads remote resources to the
    local machine.
    """

    excludes = (
        "20210114_122632.jpg",
    )

    if TYPE_CHECKING:
        bot: haruka.Haruka
        anime_images_fetch: bool
        session: aiohttp.ClientSession

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self.anime_images_fetch = False
        self.session = bot.session

    def log(self, content: str) -> None:
        self.bot.log("ASSET CLIENT: " + content)

    async def fetch_anime_images(self) -> None:
        """This function is a coroutine
        
        Asynchronously fetch the image zip file from Google Drive
        and save it to the local machine.
        """
        unzip_location = "./bot/assets/server/images"
        zip_location = unzip_location + "/collection.tar"

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
                            chunk_size = 4 * 2 ** 20  # 4 MB
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
        self.anime_images_fetch = True

    @functools.cached_property
    def files(self) -> List[str]:
        if not self.anime_images_fetch:
            raise RuntimeError("The TAR file hasn't been extracted yet.")

        _files = os.listdir("./bot/assets/server/images")
        for file in self.excludes:
            with contextlib.suppress(ValueError):
                _files.remove(file)

        return _files

    def get_anime_image(self) -> Optional[str]:
        if not self.anime_images_fetch:
            return

        if self.files:
            filename = random.choice(self.files)
            url = URL(env.get_host() + "/assets/images/" + filename)
            return str(url)

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
