import asyncio
import sys
import time

import aiohttp


async def ping(url: str) -> None:
    t = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        print(f"Created session in {time.perf_counter() - t} seconds")
        t = time.perf_counter()
        async with session.get(url) as response:
            print(f"Got response in {time.perf_counter() - t} seconds.\nResponse status: {response.status}\n")
            print(await response.text())


try:
    url = sys.argv[1]
except IndexError:
    url = input("Target host > ")

asyncio.run(ping(url))
