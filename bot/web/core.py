from __future__ import annotations

from typing import List, TYPE_CHECKING

from aiohttp import web
if TYPE_CHECKING:
    from .server import Middleware


routes = web.RouteTableDef()

# assets
routes.static("/assets", "./bot/web/assets")
routes.static("/images", "./server/images")
routes.static("/audio", "./server/audio")

# source files
routes.static("/css", "./bot/web/css")
routes.static("/script", "./bot/web/script")


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
