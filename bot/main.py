from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiohttp import web

import env
import redirector
from core import bot
from events import *
from commands import *
if TYPE_CHECKING:
    import haruka


async def runner(bot: haruka.Haruka) -> None:
    try:
        await bot.start(env.TOKEN)
    except KeyboardInterrupt:
        return


if env.BUILD_CHECK:
    print("Check success")
elif env.REDIRECT:
    web.run_app(redirector.app)
else:
    asyncio.run(runner(bot))
