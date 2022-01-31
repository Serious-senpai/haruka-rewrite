from __future__ import annotations

import io
import os
import re
import traceback
from typing import Any, Callable, Coroutine, TYPE_CHECKING

import aiohttp
import asyncpg
from aiohttp import web

import _pixiv
import env
import image
if TYPE_CHECKING:
    import haruka


PIXIV_PATH_PATTERN = re.compile(r"/image/(\d{4,8}).png/?")
HOST = env.get_host()
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

    Handler = Callable[[WebRequest], Coroutine[None, None, web.Response]]


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


@routes.get("/img")
async def _img_api(request: WebRequest) -> web.Response:
    mode = request.query.get("mode")
    category = request.query.get("category")
    try:
        image_url = await request.app.bot.image.get(category, mode=mode)
    except image.CategoryNotFound:
        raise web.HTTPNotFound
    else:
        if not image_url:
            raise web.HTTPNotFound

        result = {"url": image_url}
        return web.json_response(result)


@routes.get("/img/endpoints")
async def _img_endpoints_api(request: WebRequest) -> web.Response:
    client = request.app.bot.image
    data = {
        "sfw": list(client.sfw.keys()),
        "nsfw": list(client.nsfw.keys()),
    }
    return web.json_response(data)


@routes.get("/favicon.ico")
async def _favicon(request: WebRequest) -> web.Response:
    raise web.HTTPFound(request.app.bot.user.avatar.url)


@web.middleware
async def _img_middleware(request: WebRequest, handler: Handler) -> web.Response:
    await request.app.bot.image.wait_until_ready()
    return await handler(request)


@web.middleware
async def _pixiv_middleware(request: WebRequest, handler: Handler) -> web.Response:
    try:
        return await handler(request)
    except web.HTTPNotFound:
        match = PIXIV_PATH_PATTERN.fullmatch(request.path_qs)
        if match is not None:
            artwork_id = match.group(1)
            artwork = await _pixiv.PixivArtwork.from_id(artwork_id, session=request.app.session)
            if not artwork:
                return web.HTTPNotFound()

            try:
                await artwork.stream(session=request.app.session)
                return await handler(request)
            except BaseException as exc:
                await request.app.report_error(exc)
                return web.HTTPInternalServerError()

        raise


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

    async def report_error(self, error: Exception) -> None:
        self.log("An exception occured while running server.")
        self.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await self.bot.report("An exception has just occured in the `_server` module", send_state=False)
