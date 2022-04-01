from typing import (
    Callable,
    Coroutine,
    Literal,
    Protocol,
)

from aiohttp import web

from .app import WebApp


class WebRequest(web.Request):
    @property
    def app(self) -> WebApp: ...


class Middleware(Protocol):
    __middleware_version__: Literal[1]


Handler = Callable[[WebRequest], Coroutine[None, None, web.Response]]
