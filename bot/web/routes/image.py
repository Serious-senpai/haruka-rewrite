from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

import _image
from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/image")
async def _image_route(request: WebRequest) -> web.Response:
    mode = request.query.get("mode")
    category = request.query.get("category")
    try:
        host, url = await request.app.bot.image.get_url(category, mode=mode)
        data = {"host": host, "url": url}
    except _image.CategoryNotFound:
        raise web.HTTPNotFound
    else:
        return web.json_response(data)


@routes.get("/image/endpoints")
async def _image_endpoints_route(request: WebRequest) -> web.Response:
    client = request.app.bot.image
    data = {
        "sfw": list(client.sfw.keys()),
        "nsfw": list(client.nsfw.keys()),
    }
    return web.json_response(data)
