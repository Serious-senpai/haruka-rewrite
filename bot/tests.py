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
    "yZIXLfi8CZQ",
    "a9LDPn-MO4I",
    "IB3lcPjvWLA",
    "T4XJQO3qol8",
    "HtVdAasjOgU",
    "lqQg6PlCWgI",
    "qEJwOuvDf7I",
    "FIl7x6_3R5Y",
    "CsmdDsKjzN8",
    "sJL6WA-aGkQ",
    "Z4Vy8R84T1U",
)
ANIME_TESTS: Tuple[int, ...] = (8425,)
MANGA_TESTS: Tuple[int, ...] = (1313,)


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
        track: Optional[audio.InvidiousSource] = await audio.InvidiousSource.build(id)
        if track is None:
            log(f"Failed youtube-dl test for ID {id}: Cannot build track")
            continue

        ytdl_result: Optional[str] = await track.get_source()
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
