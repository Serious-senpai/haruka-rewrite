from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .audio import InvidiousSource
from .mal import Anime, Manga
from .nhentai import NHentai
from .pixiv import PixivArtwork
from .urban import UrbanSearch
if TYPE_CHECKING:
    import haruka


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


async def nhentai_test(bot: haruka.Haruka) -> str:
    content = make_title("NHENTAI TESTS")
    for id in NHENTAI_TESTS:
        doujin = await NHentai.get(id, session=bot.session)
        content += f"Finished NHentai test for ID {id}: {doujin}\n"

    return content


async def pixiv_test(bot: haruka.Haruka) -> str:
    content = make_title("PIXIV TESTS")
    for id in PIXIV_TESTS:
        artwork = await PixivArtwork.from_id(id, session=bot.session)
        content += f"Finished Pixiv test for ID {id}: {artwork}\n"

    return content


async def urban_test(bot: haruka.Haruka) -> str:
    content = make_title("URBAN TESTS")
    for term in URBAN_TESTS:
        result = await UrbanSearch.search(term, session=bot.session)
        content += f"Finished Urban test for term \"{term}\": {result}\n"

    return content


async def ytdl_test(bot: haruka.Haruka) -> str:
    content = make_title("YOUTUBEDL TESTS")
    for id in YTDL_TESTS:
        track = MiniInvidiousObject(id)
        ytdl_result = await InvidiousSource.get_source(track, client=bot.audio, ignore_error=True)  # type: ignore
        content += f"Finished youtube-dl test for ID {id}: {ytdl_result}\n"

    return content


async def anime_test(bot: haruka.Haruka) -> str:
    content = make_title("ANIME TESTS")
    for id in ANIME_TESTS:
        anime = await Anime.get(id, session=bot.session)
        content += f"Finished Anime test for ID {id}: {anime}\n"

    return content


async def manga_test(bot: haruka.Haruka) -> str:
    content = make_title("MANGA TESTS")
    for id in MANGA_TESTS:
        manga = await Manga.get(id, session=bot.session)
        content += f"Finished Manga test for ID {id}: {manga}\n"

    return content


async def image_test(bot: haruka.Haruka) -> str:
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


async def run_all_tests(bot: haruka.Haruka) -> None:
    logs = await asyncio.gather(
        nhentai_test(bot),
        pixiv_test(bot),
        urban_test(bot),
        ytdl_test(bot),
        anime_test(bot),
        manga_test(bot),
        image_test(bot),
    )
    bot.log("\n".join(logs))
    await bot.report("Completed all tests", send_state=False)
