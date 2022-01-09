import asyncio
from typing import Any, Callable, Optional, Tuple

import _nhentai
import _pixiv
import _urban
import audio
import mal


NHENTAI_TESTS: Tuple[int, ...] = (177013,)
PIXIV_TESTS: Tuple[int, ...] = (92390471,)
URBAN_TESTS: Tuple[str, ...] = ("paimon", "hunter")
YTDL_TESTS: Tuple[str, ...] = (
    "Hy9s13hWsoc",
    "n89SKAymNfA",
    "a9LDPn-MO4I",  # 256k DASH audio (format 141) via DASH manifest
    "IB3lcPjvWLA",  # DASH manifest with encrypted signature
    "T4XJQO3qol8",  # Controversy video
    "FIl7x6_3R5Y",  # Extraction from multiple DASH manifests (https://github.com/ytdl-org/youtube-dl/pull/6097)
    "Z4Vy8R84T1U",  # Video with unsupported adaptive stream type formats
    "sJL6WA-aGkQ",  # Geo restricted to JP
)
ANIME_TESTS: Tuple[int, ...] = (8425,)
MANGA_TESTS: Tuple[int, ...] = (1313,)


class MiniInvidiousObject:
    """Class which only contains a video ID for testing"""

    def __init__(self, id: str) -> None:
        self.id: str = id


async def nhentai_test(*, log: Callable[..., Any]) -> None:
    for id in NHENTAI_TESTS:
        doujin: Optional[_nhentai.NHentai] = await _nhentai.NHentai.get(id)
        log(f"Finished NHentai test for ID {id}: {doujin}")


async def pixiv_test(*, log: Callable[..., Any]) -> None:
    for id in PIXIV_TESTS:
        artwork: Optional[_pixiv.PixivArtwork] = await _pixiv.PixivArtwork.from_id(id)
        log(f"Finished Pixiv test for ID {id}: {artwork}")


async def urban_test(*, log: Callable[..., Any]) -> None:
    for term in URBAN_TESTS:
        result: Optional[_urban.UrbanSearch] = await _urban.UrbanSearch.search(term)
        log(f"Finished Urban test for term \"{term}\": {result}")


async def ytdl_test(*, log: Callable[..., Any]) -> None:
    for id in YTDL_TESTS:
        track: MiniInvidiousObject = MiniInvidiousObject(id)
        ytdl_result: Optional[str] = await audio.InvidiousSource.get_source(track)
        log(f"Finished youtube-dl test for ID {id}: {ytdl_result}")


async def anime_test(*, log: Callable[..., Any]) -> None:
    for id in ANIME_TESTS:
        anime: Optional[mal.Anime] = await mal.Anime.get(id)
        log(f"Finished Anime test for ID {id}: {anime}")


async def manga_test(*, log: Callable[..., Any]) -> None:
    for id in MANGA_TESTS:
        manga: Optional[mal.Manga] = await mal.Manga.get(id)
        log(f"Finished Manga test for ID {id}: {manga}")


async def run_all_tests(*, log: Callable[..., Any]) -> None:
    log("Running tests...")
    await asyncio.gather(
        nhentai_test(log=log),
        pixiv_test(log=log),
        urban_test(log=log),
        ytdl_test(log=log),
        anime_test(log=log),
        manga_test(log=log),
    )
