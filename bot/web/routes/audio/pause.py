from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/pause")
async def _pause_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if client.is_playing():
        client.pause()
        await client.notify("Paused due to web request")

    return web.Response(status=204)
