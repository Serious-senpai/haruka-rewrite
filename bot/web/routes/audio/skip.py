from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiohttp import web

from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/skip")
async def _skip_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if client.is_connected():
        asyncio.create_task(client.skip())
        await client.notify("Skipped due to web request")

    return web.Response(status=204)
