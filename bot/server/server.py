from __future__ import annotations

import asyncio
import io
import os
from typing import Any, AsyncGenerator, TYPE_CHECKING

import aiohttp
import asyncpg
import youtube_dl
from aiohttp import web


try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


if not os.path.exists("./server"):
    os.mkdir("./server")
if not os.path.exists("./server/image"):
    os.mkdir("./server/image")
if not os.path.exists("./server/audio"):
    os.mkdir("./server/audio")


async def init_db(app: WebApp) -> AsyncGenerator[None, None]:
    async with asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=2,
        max_size=10,
        max_inactive_connection_lifetime=3.0,
    ) as app.pool:
        app.log("Created connection pool")
        yield
    app.log("Closed connection pool")


async def init_session(app: WebApp) -> AsyncGenerator[None, None]:
    user_agent: str = youtube_dl.utils.random_user_agent()
    async with aiohttp.ClientSession(headers={"User-Agent": user_agent}) as app.session:
        app.log(f"Created side session, using User-Agent: {user_agent}")
        yield
    app.log("Closed side session")


if TYPE_CHECKING:
    class WebRequest(web.Request):
        @property
        def app(self) -> WebApp: ...


class WebApp(web.Application):
    if TYPE_CHECKING:
        index: str
        logfile: io.TextIOWrapper
        pool: asyncpg.Pool
        session: aiohttp.ClientSession

    def __init__(self, *args, logfile: io.TextIOWrapper, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logfile: io.TextIOWrapper = logfile
        self.cleanup_ctx.append(init_db)
        self.cleanup_ctx.append(init_session)
        self.reload()

    def reload(self) -> None:
        with open("./bot/server/index.html", "r", encoding="utf-8") as f:
            self.index = f.read()

    def log(self, content: Any) -> None:
        content: str = str(content).replace("\n", "\nSERVER | ")
        self.logfile.write(f"SERVER | {content}\n")
        self.logfile.flush()


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


with open("./log.txt", "a", encoding="utf-8") as f:
    app: WebApp = WebApp(logfile=f)
    app.add_routes(routes)
    web.run_app(app, port=os.environ.get("PORT", 8080))
