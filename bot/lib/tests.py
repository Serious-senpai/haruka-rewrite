from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .audio import InvidiousSource
from .mal import Anime, Manga
from .pixiv import PixivArtwork
from .playlist import get
from .urban import UrbanSearch
if TYPE_CHECKING:
    import haruka


PIXIV_TESTS = (92390471,)
URBAN_TESTS = ("paimon", "hunter")
YTDL_TESTS = (
    "EM4Tr4GMEa0",
    "Hy9s13hWsoc",
    "n89SKAymNfA",
    "a9LDPn-MO4I",  # 256k DASH audio (format 141) via DASH manifest
    "IB3lcPjvWLA",  # DASH manifest with encrypted signature
    "T4XJQO3qol8",  # Controversy video
    "FIl7x6_3R5Y",  # Extraction from multiple DASH manifests (https://github.com/ytdl-org/youtube-dl/pull/6097)
    "Z4Vy8R84T1U",  # Video with unsupported adaptive stream type formats
)
ANIME_TESTS = (8425,)
MANGA_TESTS = (1313,)
YTCOLLECTION_TESTS = (
    "PLP61jZvOT8I2cof9cBjAe07D8VgcfR1c5",  # YouTube playlist
    "RDEMcce0hP5SVByOVCd8UWUHEA",  # YouTube mix
)


def make_title(title: str) -> str:
    n = len(title)
    left = n // 2
    right = n - left
    return "\n" + "-" * (20 - left) + title + "-" * (20 - right) + "\n"


class MiniInvidiousObject:
    """Class which only contains a video ID for testing"""

    __slots__ = ("id",)
    if TYPE_CHECKING:
        id: str

    def __init__(self, id: str) -> None:
        self.id = id


class TestingStatus:

    __slots__ = ("bot", "success", "total")
    if TYPE_CHECKING:
        bot: haruka.Haruka
        success: int
        total: int

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot

        self.success = 0
        self.total = 0

    def update(self, success: bool) -> None:
        self.total += 1
        if success:
            self.success += 1


async def pixiv_test(status: TestingStatus) -> str:
    content = make_title("PIXIV TESTS")
    for id in PIXIV_TESTS:
        artwork = await PixivArtwork.get(id, session=status.bot.session)
        content += f"Finished Pixiv test for ID {id}: {artwork}\n"

        status.update(artwork is not None)

    return content


async def urban_test(status: TestingStatus) -> str:
    content = make_title("URBAN TESTS")
    for term in URBAN_TESTS:
        result = await UrbanSearch.search(term, session=status.bot.session)
        content += f"Finished Urban test for term \"{term}\": {result}\n"

        status.update(result is not None)

    return content


async def ytdl_test(status: TestingStatus) -> str:
    content = make_title("YOUTUBEDL TESTS")
    for id in YTDL_TESTS:
        track = MiniInvidiousObject(id)
        ytdl_result = await InvidiousSource.get_source(track, client=status.bot.audio, ignore_error=True)  # type: ignore
        content += f"Finished youtube-dl test for ID {id}: {ytdl_result}\n"

        status.update(ytdl_result is not None)

    return content


async def anime_test(status: TestingStatus) -> str:
    content = make_title("ANIME TESTS")
    for id in ANIME_TESTS:
        anime = await Anime.get(id, session=status.bot.session)
        content += f"Finished Anime test for ID {id}: {anime}\n"

        status.update(anime is not None)

    return content


async def manga_test(status: TestingStatus) -> str:
    content = make_title("MANGA TESTS")
    for id in MANGA_TESTS:
        manga = await Manga.get(id, session=status.bot.session)
        content += f"Finished Manga test for ID {id}: {manga}\n"

        status.update(manga is not None)

    return content


async def image_test(status: TestingStatus) -> str:
    bot = status.bot
    await bot.image.wait_until_ready()
    content = make_title("IMAGE TESTS")

    checked = set()
    for category, sources in bot.image.sfw.items():
        for source in sources:
            if source not in checked:
                checked.add(source)
                url = await source.get(category)
                status.update(url is not None)
                if url is None:
                    content += f"Test failed for {source} when requesting SFW {category}\n"
                else:
                    content += f"Finished test for {source} when requesting SFW {category}: {url}\n"

    checked.clear()
    for category, sources in bot.image.nsfw.items():
        for source in sources:
            if source not in checked:
                checked.add(source)
                url = await source.get(category, mode="nsfw")
                status.update(url is not None)
                if url is None:
                    content += f"Test failed for {source} when requesting NSFW {category}\n"
                else:
                    content += f"Finished test for {source} when requesting NSFW {category}: {url}\n"

    return content


async def ytcollection_test(status: TestingStatus) -> str:
    content = make_title("YOUTUBE COLLECTION TEST")
    for id in YTCOLLECTION_TESTS:
        result = await get(id, session=status.bot.session)
        content += f"Finished ytcollection test for {id}: {result}\n"

        status.update(result is not None)


async def run_all_tests(bot: haruka.Haruka) -> None:
    status = TestingStatus(bot)
    logs = await asyncio.gather(
        pixiv_test(status),
        urban_test(status),
        ytdl_test(status),
        anime_test(status),
        manga_test(status),
        image_test(status),
    )
    bot.log("\n".join(logs))
    await bot.report(f"Completed all tests: {status.success}/{status.total} passed", send_state=False)
