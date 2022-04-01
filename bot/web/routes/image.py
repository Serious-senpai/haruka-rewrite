from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from lib import image
from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/image")
async def _image_route(request: WebRequest) -> web.Response:
    try:
        mode = request.query["mode"]
        category = request.query["category"]
        if mode not in ("sfw", "nsfw"):
            raise KeyError

    except KeyError:
        raise web.HTTPBadRequest

    try:
        host, url = await request.app.bot.image.get_url(category, mode=mode)
        data = {"host": host, "url": url}
    except image.CategoryNotFound:
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
