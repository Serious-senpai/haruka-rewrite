import asyncio
from typing import AnyStr, IO


async def write(file: IO[AnyStr], data: AnyStr) -> None:
    await asyncio.to_thread(file.write, data)
