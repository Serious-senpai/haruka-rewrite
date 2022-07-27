from __future__ import annotations

import asyncio
import contextlib
import re
from typing import List, Union

import aiohttp

from .artwork import PixivArtwork
from .exceptions import NSFWArtworkDetected


__all__ = (
    "ID_PATTERN",
    "URL_PATTERN",
    "parse",
)
ID_PATTERN = re.compile(r"(?<!\d)\d{4,9}(?!\d)")
URL_PATTERN = re.compile(r"https://www\.pixiv\.net/(en/)?artworks/(\d{4,9})/?")


def raise_for_nsfw(artwork: PixivArtwork) -> None:
    if artwork.nsfw:
        raise NSFWArtworkDetected(artwork)


async def parse(query: str, *, session: aiohttp.ClientSession) -> Union[PixivArtwork, List[PixivArtwork]]:
    """This function is a coroutine

    Parse ``query`` to predict the user's intention when processing a
    Pixiv-related request.

    Note that this coroutine never returns ``None``. When no result is
    found, an empty list is returned.

    Parameters
    -----
    query: ``str``
        The input string
    session: ``aiohttp.ClientSession``
        The session to perform the request

    Returns
    -----
    Union[``PixivArtwork``, List[``PixivArtwork``]]
        A certain artwork (when an ID or URL is detected), or multiple
        artworks as a list (in case of a searching string)
    """
    match = ID_PATTERN.fullmatch(query)
    if match:
        artwork = await PixivArtwork.get(match.group(), session=session)
        if artwork:
            raise_for_nsfw(artwork)
            return artwork

    if query.startswith("http"):
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            async with session.get(query) as response:
                if response.ok:
                    match = URL_PATTERN.fullmatch(str(response.url))
                    if match is not None:
                        artwork = await PixivArtwork.get(match.group(2), session=session)
                        if artwork:
                            raise_for_nsfw(artwork)
                            return artwork

    return await PixivArtwork.search(query, session=session)
