from __future__ import annotations

from typing import (
    runtime_checkable,
    Callable,
    Coroutine,
    Literal,
    Protocol,
    TYPE_CHECKING,
)


if not TYPE_CHECKING:
    raise ImportError("This module only exists for type checking")


from aiohttp import web

from .app import WebApp


class WebRequest(web.Request):
    @property
    def app(self) -> WebApp: ...


Handler = Callable[[WebRequest], Coroutine[None, None, web.Response]]


@runtime_checkable
class Middleware(Protocol, Callable[[WebRequest, Handler], web.Response]):
    __middleware_version__: Literal[1]
