from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..types import WebRequest


@routes.get("/reload")
async def _reload_route(request: WebRequest) -> web.Response:
    request.app.reload()
    raise web.HTTPFound("/")
