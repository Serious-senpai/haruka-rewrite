from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/collection")
async def _collection_route(request: WebRequest) -> web.Response:
    client = request.app.bot.asset_client
    image_url = client.get_anime_image()
    if image_url is None:
        raise web.HTTPServiceUnavailable

    response = {
        "url": image_url,
    }
    return web.json_response(response)
