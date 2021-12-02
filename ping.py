import aiohttp
import asyncio
import sys
import time


async def ping(url: str):
    t = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        print(f"Created session in {time.perf_counter() - t} seconds")
        t = time.perf_counter()
        async with session.get(url) as response:
            print(f"Got response in {time.perf_counter() - t} seconds.\nResponse status: {response.status}\n")
            print(await response.text())


try:
    asyncio.run(ping(sys.argv[1]))
except IndexError:
    url = input("Target host > ")
    try:
        asyncio.run(ping(url))
    except Exception as ex:
        print(f"{ex.__class__.__name__}: {ex}")
except Exception as ex:
    print(f"{ex.__class__.__name__}: {ex}")
