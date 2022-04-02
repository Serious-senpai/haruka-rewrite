from typing import (
    Callable,
    Coroutine,
)

from aiohttp import web, web_app

from .app import WebApp


class WebRequest(web.Request):
    @property
    def app(self) -> WebApp: ...


Middleware = web_app._Middleware
Handler = Callable[[WebRequest], Coroutine[None, None, web.Response]]
