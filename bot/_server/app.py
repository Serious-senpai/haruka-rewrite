from __future__ import annotations

import io
import traceback
from typing import Any, TYPE_CHECKING

import aiohttp
import asyncpg
from aiohttp import web

from .core import middleware_group, routes
if TYPE_CHECKING:
    import haruka


class WebApp(web.Application):

    if TYPE_CHECKING:
        bot: haruka.Haruka
        pool: asyncpg.Pool
        logfile: io.TextIOWrapper
        session: aiohttp.ClientSession

    def __init__(self, *, bot: haruka.Haruka) -> None:
        self.bot = bot
        self.pool = self.bot.conn
        self.logfile = self.bot.logfile
        self.session = self.bot.session

        super().__init__(middlewares=middleware_group.to_list())
        self.add_routes(routes)
        self.reload()

    def reload(self) -> None:
        with open("./bot/_server/index.html", "r", encoding="utf-8") as f:
            self.index = f.read()

    def log(self, content: Any) -> None:
        content = str(content).replace("\n", "\nSERVER | ")
        self.logfile.write(f"SERVER | {content}\n")
        self.logfile.flush()

    async def report_error(self, error: Exception) -> None:
        self.log("An exception occured while running server.")
        self.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await self.bot.report("An exception has just occured in the `_server` module", send_state=False)
