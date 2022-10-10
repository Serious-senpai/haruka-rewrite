import asyncio
import contextlib
import time
from typing import List

import aiohttp


TIMEOUT = aiohttp.ClientTimeout(total=15)
INVIDIOUS_URLS = [
    "https://invidious.snopyta.org",
    "https://invidio.xamh.de",
    "https://yewtu.be",
    "https://vid.puffyan.us",
    "https://invidious-us.kavin.rocks",
    "https://inv.riverside.rocks",
    "https://vid.mint.lgbt",
    "https://invidious-jp.kavin.rocks",
    "https://invidious.osi.kr",
    "https://yt.artemislena.eu",
    "https://youtube.076.ne.jp",
    "https://invidious.namazso.eu",
    "https://invidious.kavin.rocks",
]


async def initialize_hosts(session: aiohttp.ClientSession) -> List[str]:
    """This function is a coroutine

    Make a dummy request to all Invidious instances and sort
    the hosts according to their response time.

    Hosts which timed out or didn't response with HTTP 200 will
    be removed.

    Parameters
    -----
    session: ``aiohttp.ClientSession``
        The session to perform the dummy requests

    Returns
    -----
    List[``str``]
        The list object containing the sorted hosts
    """
    hosts = {}

    global INVIDIOUS_URLS
    for url in INVIDIOUS_URLS:
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            _start_timestamp = time.perf_counter()
            async with session.get(url, timeout=TIMEOUT) as response:
                if response.status == 200:
                    ping = time.perf_counter() - _start_timestamp
                    hosts[url] = ping

    INVIDIOUS_URLS = sorted(hosts.keys(), key=hosts.__getitem__)
    return INVIDIOUS_URLS
