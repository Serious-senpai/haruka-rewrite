from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/stopafter")
async def _stopafter_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if await client.switch_stopafter():
        await client.notify("Enabled `stopafter` due to web request. This will be the last song to be played.")
    else:
        await client.notify("Disabled `stopafter` due to web request. Other songs will be played normally after this one ends.")

    return web.Response(status=204)
