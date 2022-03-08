from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING

import aiohttp
if TYPE_CHECKING:
    import haruka


ANIME_IMAGES_URL = "https://drive.google.com/uc?id=1J8gan17hSLrS46ILPYXggU5o-8yh-0uA&export=download&confirm=t"


if not os.path.isdir("./bot/assets/server/images"):
    os.mkdir("./bot/assets/server/images")


class AssetClient:
    """Represents a client that downloads remote resources to the
    local machine.
    """

    if TYPE_CHECKING:
        bot: haruka.Haruka
        session: aiohttp.ClientSession

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self.session = bot.session

    async def fetch_anime_images(self) -> None:
        """This function is a coroutine
        
        Asynchronously fetch the image zip file from Google Drive
        and save it to the local machine.
        """
        unzip_location = "./bot/assets/server/images"
        zip_location = unzip_location + "/collection.zip"

        async with self.session.get(ANIME_IMAGES_URL) as response:
            if response.status == 200:
                with open(zip_location, "wb", buffering=0) as f:
                    while data := await response.content.read(4096):
                        f.write(data)
                        f.flush()
            else:
                self.bot.log(f"Cannot fetch images from {ANIME_IMAGES_URL}: HTTP status {response.status}")
                return

        if sys.platform == "linux":
            args = (
                "unzip",
                "-q",
                zip_location,
                "-d", unzip_location,
            )
        elif sys.platform == "win32":
            args = (
                "7z",
                "e",
                "-bd",
                zip_location,
                f"-o{unzip_location}"
            )
        else:
            self.bot.log(f"Unsupported platform {sys.platform}")
            return

        process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
        _, _stderr = await process.communicate()
        if _stderr:
            stderr = _stderr.decode("utf-8")
            self.bot.log("WARNING: Anime images fetching subprocess stderr:\n" + stderr)
