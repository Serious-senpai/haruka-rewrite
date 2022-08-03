from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/reload")
async def _reload_route(request: WebRequest) -> web.Response:
    request.app.loader.clear()

    data = {"success": True}
    return web.json_response(data)
