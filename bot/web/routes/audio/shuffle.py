from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/shuffle")
async def _shuffle_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if await client.switch_shuffle():
        await client.notify("Shuffle has been turned on due to web request. Songs will be played randomly.")
    else:
        await client.notify("Shuffle has been turned off due to web request. Songs will be played with the queue order.")

    return web.Response(status=204)
