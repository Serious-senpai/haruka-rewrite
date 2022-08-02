from __future__ import annotations

import io
import traceback
from typing import Any, TYPE_CHECKING

import aiohttp
import asyncpg
from aiohttp import web

from .core import middleware_group, routes
from .loader import TextFileLoader
if TYPE_CHECKING:
    import haruka


class WebApp(web.Application):

    if TYPE_CHECKING:
        bot: haruka.Haruka
        pool: asyncpg.Pool
        logfile: io.TextIOWrapper
        session: aiohttp.ClientSession
        loader: TextFileLoader

    def __init__(self, bot: haruka.Haruka) -> None:
        self.bot = bot
        self.pool = self.bot.conn
        self.logfile = self.bot.logfile
        self.session = self.bot.session

        self.loader = TextFileLoader()

        super().__init__(middlewares=middleware_group.to_list())
        self.add_routes(routes)

    def log(self, content: Any) -> None:
        prefix = "[SERVER] "
        content = str(content).replace("\n", f"\n{prefix}")
        self.logfile.write(f"{prefix}{content}\n")
        self.logfile.flush()

    async def report_error(self, error: BaseException) -> None:
        self.log("An exception occured while running server.")
        self.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await self.bot.report("An exception has just occured in the `server` module", send_state=False)
