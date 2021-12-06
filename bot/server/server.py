import asyncio
import contextlib
import html
import os
import signal
from io import TextIOWrapper
from typing import Any, List, Optional

import aiohttp
import asyncpg
from aiohttp import web


if not os.path.exists("./server"):
    os.mkdir("./server")
if not os.path.exists("./server/image"):
    os.mkdir("./server/image")
if not os.path.exists("./server/video"):
    os.mkdir("./server/video")


class HTMLPage:

    __slots__ = (
        "_page",
    )

    def __init__(self) -> None:
        with open("./bot/server/index.html", "r", encoding="utf-8") as f:
            self._page: str = f.read()

    @property
    def page(self) -> str:
        return self._page

    def split(self, category: str) -> List[str]:
        return self.page.split(f"<!--{category}-->")

    def edit(self, category: str, content: str) -> str:
        parts: List[str] = self.split(category)
        return content.join(parts[::2])

    def remove(self, category: str) -> str:
        return self.edit(category, "")


class WebApp:

    __slots__ = (
        "pool",
        "loop",
        "session",
        "logfile",
        "index",
        "runner",
    )

    def __init__(self) -> None:
        routes: web.RouteTableDef = web.RouteTableDef()
        routes.static("/asset", "./bot/assets/server")
        routes.static("/image", "./server/image")
        routes.static("/video", "./server/video")

        app: web.Application = web.Application()
        app.add_routes(routes)
        app.add_routes(
            [
                web.get("/", self._main_page),
                web.get("/reload", self._reload_page),
                web.get("/playlist", self._playlist_search_page),
            ]
        )
        self.runner: web.AppRunner = web.AppRunner(app)

        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.logfile: TextIOWrapper = open("./log.txt", "a", encoding="utf-8")
        signal.signal(signal.SIGTERM, self.kill)
        self.reload()

    def reload(self) -> None:
        self.index: HTMLPage = HTMLPage()

    def run(self) -> None:
        try:
            self.loop.run_until_complete(self.start())
        finally:
            self.loop.run_until_complete(self.cleanup())

    async def start(self) -> None:
        self.pool: asyncpg.Pool = await asyncpg.create_pool(
            os.environ["DATABASE_URL"],
            min_size=2,
            max_size=10,
            max_inactive_connection_lifetime=3.0,
        )
        self.log("Created connection pool for server")
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.log("Created side session for server")
        port: int = int(os.environ.get("PORT", "8080"))

        try:
            await self.runner.setup()
            site: web.TCPSite = web.TCPSite(self.runner, None, port)
            await site.start()
            self.log(f"Started server on port {port}")
            print(f"Started server on port {port}")
            while True:
                await asyncio.sleep(3600)
        except (web.GracefulExit, KeyboardInterrupt):
            pass

    def kill(self, *args) -> None:
        print("Received SIGTERM signal. Terminating server...")
        self.log("Received SIGTERM signal. Terminating server...")
        self.loop.create_task(self.cleanup())

    async def cleanup(self) -> None:
        await self.pool.close()
        self.log("Closed connection pool for server.")
        await self.session.close()
        self.log("Closed side session for server.")
        await self.runner.cleanup()
        self.log("Closed server")
        self.logfile.close()

    def log(self, content: Any) -> None:
        content: str = str(content).replace("\n", "\nSERVER | ")
        self.logfile.write(f"SERVER | {content}\n")
        self.logfile.flush()

    # Web endpoints

    async def _main_page(self, request: web.Request) -> web.Response:
        return web.Response(
            text=self.index.page,
            status=200,
            content_type="text/html",
        )

    async def _reload_page(self, request: web.Request) -> web.Response:
        await asyncio.to_thread(self.reload)
        raise web.HTTPFound("/")

    async def _playlist_search_page(self, request: web.Request) -> web.Response:
        query: Optional[str] = request.query.get("query")
        if not query:
            raise web.HTTPFound("/")

        rows: List[asyncpg.Record] = await self.pool.fetch(
            """SELECT *
            FROM playlist
            WHERE similarity(title, $1) > 0.35
            ORDER BY similarity(title, $1)
            LIMIT 6;
            """,
            query,
        )

        content: str
        value: str

        if not rows:
            content = "No matching result was found."
        else:
            content = "<tr><th>ID</th><th>Title</th><th>Description</th><th>Discord author ID</th><th>Number of songs</th></tr>"
            for row in rows:
                content += "<tr>"
                for key in (
                    "id",
                    "title",
                    "description",
                    "author_id",
                ):
                    value = str(row[key])
                    content += f"<td>{html.escape(value)}</td>"
                content += f"<td>{len(row['queue'])}</td>"
                content += "</tr>"
            content = "<table>" + content + "</table>"

        return web.Response(
            text=self.index.edit("Menu", content),
            status=200,
            content_type="text/html",
        )


app: WebApp = WebApp()
with contextlib.suppress(KeyboardInterrupt):
    app.run()
