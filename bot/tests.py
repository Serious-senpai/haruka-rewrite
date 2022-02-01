import asyncio
from typing import Any, Callable, TYPE_CHECKING

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


class MiniInvidiousObject:
    """Class which only contains a video ID for testing"""

    if TYPE_CHECKING:
        id: str

    def __init__(self, id: str) -> None:
        self.id = id


async def nhentai_test(*, log: Callable[..., Any]) -> None:
    for id in NHENTAI_TESTS:
        doujin = await _nhentai.NHentai.get(id)
        log(f"Finished NHentai test for ID {id}: {doujin}")


async def pixiv_test(*, log: Callable[..., Any]) -> None:
    for id in PIXIV_TESTS:
        artwork = await _pixiv.PixivArtwork.from_id(id, session=bot.session)
        log(f"Finished Pixiv test for ID {id}: {artwork}")


async def urban_test(*, log: Callable[..., Any]) -> None:
    for term in URBAN_TESTS:
        result = await _urban.UrbanSearch.search(term)
        log(f"Finished Urban test for term \"{term}\": {result}")


async def ytdl_test(*, log: Callable[..., Any]) -> None:
    for id in YTDL_TESTS:
        track = MiniInvidiousObject(id)
        ytdl_result = await audio.InvidiousSource.get_source(track)
        log(f"Finished youtube-dl test for ID {id}: {ytdl_result}")


async def anime_test(*, log: Callable[..., Any]) -> None:
    for id in ANIME_TESTS:
        anime = await mal.Anime.get(id)
        log(f"Finished Anime test for ID {id}: {anime}")


async def manga_test(*, log: Callable[..., Any]) -> None:
    for id in MANGA_TESTS:
        manga = await mal.Manga.get(id)
        log(f"Finished Manga test for ID {id}: {manga}")


async def image_test(*, log: Callable[..., Any]) -> None:
    await bot.image.wait_until_ready()
    checked = []
    for category, sources in bot.image.sfw.items():
        for source in sources:
            if source not in checked:
                checked.append(source)
                url = await source.get(category)
                if url is None:
                    log(f"Test failed for {source.__class__.__name__}, category {category}")
                else:
                    log(f"Finished image test for {source.__class__.__name__} (category {category}): {url}")


async def run_all_tests() -> None:
    await asyncio.gather(
        nhentai_test(log=bot.log),
        pixiv_test(log=bot.log),
        urban_test(log=bot.log),
        ytdl_test(log=bot.log),
        anime_test(log=bot.log),
        manga_test(log=bot.log),
        image_test(log=bot.log),
    )
