import asyncio
from typing import Optional, Tuple

import _nhentai
import _pixiv
import _urban
import audio
import mal
from core import bot


NHENTAI_TESTS: Tuple[int, ...] = (177013,)
PIXIV_TESTS: Tuple[int, ...] = (92390471,)
URBAN_TESTS: Tuple[str, ...] = ("Paimon",)
YTDL_TESTS: Tuple[str, ...] = ("Hy9s13hWsoc", "n89SKAymNfA")
ANIME_TESTS: Tuple[int, ...] = (8425,)
MANGA_TESTS: Tuple[int, ...] = (1313,)


async def nhentai_test() -> None:
    for id in NHENTAI_TESTS:
        doujin: Optional[_nhentai.NHentai] = await _nhentai.NHentai.get(id)
        bot.log(f"Finished NHentai test for ID {id}: {doujin}")


async def pixiv_test() -> None:
    for id in PIXIV_TESTS:
        artwork: Optional[_pixiv.PixivArtwork] = await _pixiv.PixivArtwork.from_id(id)
        bot.log(f"Finished Pixiv test for ID {id}: {artwork}")


async def urban_test() -> None:
    for term in URBAN_TESTS:
        result: Optional[_urban.UrbanSearch] = await _urban.UrbanSearch.search(term)
        bot.log(f"Finished Urban test for term {term}: {result}")


async def ytdl_test() -> None:
    for id in YTDL_TESTS:
        track: Optional[audio.InvidiousSource] = await audio.InvidiousSource.build(id)
        if track is None:
            bot.log(f"Failed youtube-dl test for ID {id}: Cannot build track")
            return

        ytdl_result: Optional[str] = await track.get_source()
        bot.log(f"Finished youtube-dl test for ID {id}: {ytdl_result}")


async def anime_test() -> None:
    for id in ANIME_TESTS:
        anime: Optional[mal.Anime] = await mal.Anime.get(id)
        bot.log(f"Finished Anime test for ID {id}: {anime}")


async def manga_test() -> None:
    for id in MANGA_TESTS:
        manga: Optional[mal.Manga] = await mal.Manga.get(id)
        bot.log(f"Finished Manga test for ID {id}: {manga}")


async def run_all_tests() -> None:
    bot.log("Running tests...")
    await asyncio.gather(
        nhentai_test(),
        pixiv_test(),
        urban_test(),
        ytdl_test(),
        anime_test(),
        manga_test(),
    )
