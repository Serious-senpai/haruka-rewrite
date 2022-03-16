from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/collection")
async def _collection_route(request: WebRequest) -> web.Response:
    client = request.app.bot.asset_client
    path = client.get_anime_image_path()
    if path is None:
        raise web.HTTPServiceUnavailable

    raise web.HTTPFound(path)
