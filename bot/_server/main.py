from __future__ import annotations

import io
import os
import re
from typing import Any, Callable, Coroutine, TYPE_CHECKING

import aiohttp
import asyncpg
from aiohttp import web

import _pixiv
if TYPE_CHECKING:
    import haruka


PIXIV_PATH_PATTERN = re.compile(r"/image/(\d{4,8}).png/?")
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


routes = web.RouteTableDef()
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


@routes.get("/favicon.ico")
async def _favicon(request: WebRequest) -> web.Response:
    raise web.HTTPFound(request.app.bot.user.avatar.url)


@web.middleware
async def _pixiv_middleware(request: WebRequest, handler: Callable[[WebRequest], Coroutine[None, None, web.Response]]) -> web.Response:
    try:
        response = await handler(request)
    except web.HTTPNotFound as exc:
        match = PIXIV_PATH_PATTERN.fullmatch(request.path_qs)
        if match:
            artwork_id = match.group(1)
            artwork = await _pixiv.PixivArtwork.from_id(artwork_id, session=request.app.session)
            if not artwork:
                raise

            try:
                await artwork.stream(session=request.app.session)
            except _pixiv.StreamError:
                raise exc

            with open(f"./server/image/{artwork_id}.png", "rb") as f:
                return web.Response(body=f.read(), status=304, content_type="application/octet-stream")

        raise

    return response


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

        super().__init__(middlewares=[
            _pixiv_middleware,
        ])
        self.add_routes(routes)
        self.reload()

    def reload(self) -> None:
        with open("./bot/_server/index.html", "r", encoding="utf-8") as f:
            self.index = f.read()

    def log(self, content: Any) -> None:
        content = str(content).replace("\n", "\nSERVER | ")
        self.logfile.write(f"SERVER | {content}\n")
        self.logfile.flush()
