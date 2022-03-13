import asyncio
from typing import TYPE_CHECKING

import _nhentai
import _pixiv
import _urban
import audio
import mal
from core import bot


NHENTAI_TESTS = (177013,)
PIXIV_TESTS = (92390471,)
URBAN_TESTS = ("paimon", "hunter")
YTDL_TESTS = (
    "Hy9s13hWsoc",
    "n89SKAymNfA",
    "a9LDPn-MO4I",  # 256k DASH audio (format 141) via DASH manifest
    "IB3lcPjvWLA",  # DASH manifest with encrypted signature
    "T4XJQO3qol8",  # Controversy video
    "FIl7x6_3R5Y",  # Extraction from multiple DASH manifests (https://github.com/ytdl-org/youtube-dl/pull/6097)
    "Z4Vy8R84T1U",  # Video with unsupported adaptive stream type formats
    "sJL6WA-aGkQ",  # Geo restricted to JP
)
ANIME_TESTS = (8425,)
MANGA_TESTS = (1313,)


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


async def nhentai_test() -> str:
    content = make_title("NHENTAI TESTS")
    for id in NHENTAI_TESTS:
        doujin = await _nhentai.NHentai.get(id)
        content += f"Finished NHentai test for ID {id}: {doujin}\n"

    return content


async def pixiv_test() -> str:
    content = make_title("PIXIV TESTS")
    for id in PIXIV_TESTS:
        artwork = await _pixiv.PixivArtwork.from_id(id, session=bot.session)
        content += f"Finished Pixiv test for ID {id}: {artwork}\n"

    return content


async def urban_test() -> str:
    content = make_title("URBAN TESTS")
    for term in URBAN_TESTS:
        result = await _urban.UrbanSearch.search(term)
        content += f"Finished Urban test for term \"{term}\": {result}\n"

    return content


async def ytdl_test() -> str:
    content = make_title("YOUTUBEDL TESTS")
    for id in YTDL_TESTS:
        track = MiniInvidiousObject(id)
        ytdl_result = await audio.InvidiousSource.get_source(track, ignore_error=True)
        content += f"Finished youtube-dl test for ID {id}: {ytdl_result}\n"

    return content


async def anime_test() -> str:
    content = make_title("ANIME TESTS")
    for id in ANIME_TESTS:
        anime = await mal.Anime.get(id)
        content += f"Finished Anime test for ID {id}: {anime}\n"

    return content


async def manga_test() -> str:
    content = make_title("MANGA TESTS")
    for id in MANGA_TESTS:
        manga = await mal.Manga.get(id)
        content += f"Finished Manga test for ID {id}: {manga}\n"

    return content


async def image_test() -> str:
    await bot.image.wait_until_ready()
    checked = []
    content = make_title("IMAGE TESTS")
    for category, sources in bot.image.sfw.items():
        for source in sources:
            if source not in checked:
                checked.append(source)
                url = await source.get(category)
                if url is None:
                    content += f"Test failed for {source.__class__.__name__}, category {category}\n"
                else:
                    content += f"Finished image test for {source.__class__.__name__} (category {category}): {url}\n"

    return content


async def run_all_tests() -> None:
    logs = await asyncio.gather(
        nhentai_test(),
        pixiv_test(),
        urban_test(),
        ytdl_test(),
        anime_test(),
        manga_test(),
        image_test(),
    )
    bot.log("\n".join(logs))
    await bot.report("Completed all tests", send_state=False)
