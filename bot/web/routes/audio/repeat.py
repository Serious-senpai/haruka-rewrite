from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/repeat")
async def _repeat_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if await client.switch_repeat():
        await client.notify("Switched to `REPEAT ONE` mode. The current song will be played repeatedly.")
    else:
        await client.notify("Switched to `REPEAT ALL` mode. All songs will be played as normal.")

    return web.Response(status=204)
