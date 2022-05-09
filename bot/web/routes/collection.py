from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/collection")
async def _collection_route(request: WebRequest) -> web.Response:
    client = request.app.bot.asset_client
    url = client.get_anime_image()
    if url is None:
        raise web.HTTPServiceUnavailable

    return web.json_response({"url": url})


@routes.get("/collection/list")
async def _collection_list_route(request: WebRequest) -> web.Response:
    results = request.app.bot.asset_client.list_images()
    if results is None:
        raise web.HTTPServiceUnavailable

    return web.json_response(results)
