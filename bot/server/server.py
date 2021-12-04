import asyncio
import html
import os
from typing import List, Optional

import aiohttp
import asyncpg
from aiohttp import web


if not os.path.exists("./server"):
    os.mkdir("./server")
if not os.path.exists("./server/image"):
    os.mkdir("./server/image")
with open("./bot/server/index.html", "r", encoding="utf-8") as f:
    index: str = f.read()


class WebApp:

    __slots__ = (
        "app",
        "routes",
        "pool",
        "loop",
        "session",
    )

    def __init__(self) -> None:
        self.routes: web.RouteTableDef = web.RouteTableDef()
        self.routes.static("/asset", "./bot/assets/server")

        self.app: web.Application = web.Application()
        self.app.add_routes(self.routes)
        self.app.add_routes(
            [
                web.get("/", self._main_page),
                web.get("/search", self._search),
            ]
        )

        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        try:
            self.loop.run_until_complete(self.start())
        finally:
            self.loop.run_until_complete(self.cleanup())

            tasks: List[asyncio.Task] = []
            for task in asyncio.all_tasks(loop=self.loop):
                task.cancel()
                tasks.append(task)

            try:
                self.loop.run_until_complete(asyncio.gather(*tasks))
            except asyncio.CancelledError:
                pass
            print(f"Cleaned up {len(tasks)} tasks")

    async def start(self) -> None:
        self.pool: asyncpg.Pool = await asyncpg.create_pool(
            os.environ["DATABASE_URL"],
            min_size=2,
            max_size=10,
            max_inactive_connection_lifetime=3.0,
        )
        print("Created connection pool for server")
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        print("Created side session for server")

        try:
            await web._run_app(self.app, port=int(os.environ.get("PORT", 8080)))
        except (web.GracefulExit, KeyboardInterrupt):
            pass

    async def _main_page(self, request: web.Request) -> web.Response:
        return web.Response(
            text=index,
            status=200,
            content_type="text/html",
        )

    async def _search(self, request: web.Request) -> web.Response:
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
            text=index.replace("<!--results-->", content),
            status=200,
            content_type="text/html",
        )

    async def cleanup(self) -> None:
        await self.pool.close()
        print("Closed connection pool for server.")
        await self.session.close()
        print("Closed side session for server.")


try:
    app: WebApp = WebApp()
except KeyboardInterrupt:
    # Why this get re-raised here?
    pass
