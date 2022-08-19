from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/audio-control")
async def _audio_control_route(request: WebRequest) -> web.Response:
    try:
        key = request.query["key"]
    except KeyError:
        raise web.HTTPBadRequest
    else:
        raise web.HTTPFound(f"/?audio-control=1&key={key}")


@routes.get("/audio-control/playing")
async def _audio_control_playing_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if not client.current_track:
        raise web.HTTPNotFound

    data = {
        "thumbnail": client.current_track.thumbnail,
        "title": client.current_track.title,
        "description": client.current_track.description,
    }
    return web.json_response(data)
