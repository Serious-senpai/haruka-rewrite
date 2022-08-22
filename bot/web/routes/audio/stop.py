from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/stop")
async def _stop_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if client.is_connected():
        await client.disconnect(force=True)
        await client.notify("Stopped due to web request")

    return web.Response(status=204)
