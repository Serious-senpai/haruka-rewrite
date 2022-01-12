from __future__ import annotations

import io
import os
from typing import Any, TYPE_CHECKING

import aiohttp
import asyncpg
from aiohttp import web

if TYPE_CHECKING:
    import haruka


if not os.path.exists("./server"):
    os.mkdir("./server")
if not os.path.exists("./server/image"):
    os.mkdir("./server/image")
if not os.path.exists("./server/audio"):
    os.mkdir("./server/audio")


if TYPE_CHECKING:
    class WebRequest(web.Request):
        @property
        def app(self) -> WebApp: ...


routes: web.RouteTableDef = web.RouteTableDef()
routes.static("/assets", "./bot/assets/server")
routes.static("/image", "./server/image")
routes.static("/audio", "./server/audio")


@routes.get("/")
async def _main_page(request: WebRequest) -> web.Response:
    return web.Response(
        text=request.app.index,
        status=200,
        content_type="text/html",
    )


@routes.get("/reload")
async def _reload_page(request: WebRequest) -> web.Response:
    request.app.reload()
    raise web.HTTPFound("/")


class WebApp(web.Application):
    if TYPE_CHECKING:
        index: str
        logfile: io.TextIOWrapper
        pool: asyncpg.Pool
        session: aiohttp.ClientSession
        bot: haruka.Haruka

    def __init__(self, *args, **kwargs) -> None:
        self.bot: haruka.Haruka = kwargs.pop("bot")
        self.pool: asyncpg.Pool = self.bot.conn
        self.logfile: io.TextIOWrapper = self.bot.logfile
        self.session: aiohttp.ClientSession = self.bot.session

        super().__init__(*args, **kwargs)
        self.add_routes(routes)
        self.reload()

    def reload(self) -> None:
        with open("./bot/server/index.html", "r", encoding="utf-8") as f:
            self.index = f.read()

    def log(self, content: Any) -> None:
        content: str = str(content).replace("\n", "\nSERVER | ")
        self.logfile.write(f"SERVER | {content}\n")
        self.logfile.flush()
