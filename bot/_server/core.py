from __future__ import annotations

from typing import List, TYPE_CHECKING

from aiohttp import web
if TYPE_CHECKING:
    from ._types import Middleware, WebRequest


routes = web.RouteTableDef()
routes.static("/assets", "./bot/assets/server")
routes.static("/images", "./server/images")
routes.static("/audio", "./server/audio")


@routes.get("/favicon.ico")
async def _favicon(request: WebRequest) -> web.Response:
    raise web.HTTPFound(request.app.bot.user.avatar.url)


class MiddlewareGroup:

    if TYPE_CHECKING:
        middlewares: List[Middleware]

    def __init__(self, *middlewares) -> None:
        self.middlewares = list(middlewares)

    def middleware(self, func: Middleware) -> Middleware:
        self.middlewares.append(func)
        return func

    def to_list(self) -> List[Middleware]:
        return self.middlewares


middleware_group = MiddlewareGroup()
