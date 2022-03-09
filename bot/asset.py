from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

import aiohttp
from bs4 import BeautifulSoup
if TYPE_CHECKING:
    import haruka


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
        zip_location = unzip_location + "/collection.tar"

        async with self.session.get("https://www.mediafire.com/file/uw42hxy45psweoa/Collection.tar/file") as response:
            if response.status == 200:
                html = await response.text(encoding="utf-8")
                soup = BeautifulSoup(html, "html.parser")
                download_button = soup.find("a", attrs={"class": "input popsok"})
                file_url = download_button.get("href")

                if not file_url:
                    return self.bot.log(f"Cannot obtain a download URL from this element:\n{download_button}")
                    
            else:
                return self.bot.log(f"Cannot fetch download URL for anime images: HTTP status {response.status}")

        async with self.session.get(file_url) as response:
            if response.status == 200:
                with open(zip_location, "wb", buffering=0) as f:
                    while data := await response.content.read(4096):
                        f.write(data)
            else:
                return self.bot.log(f"Cannot fetch anime images from {file_url}: HTTP status {response.status}")

        args = (
            "tar",
            "-xf", zip_location,
            "-C", unzip_location,
        )

        process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
        _, _stderr = await process.communicate()
        if _stderr:
            stderr = _stderr.decode("utf-8")
            self.bot.log("WARNING: Anime images fetching subprocess stderr:\n" + stderr)
