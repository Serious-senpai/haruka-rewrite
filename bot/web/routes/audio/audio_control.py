from __future__ import annotations

import io
from typing import TYPE_CHECKING

import aiohttp
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
        "title": client.current_track.title,
        "description": client.current_track.description,
    }
    return web.json_response(data)


@routes.get("/audio-control/thumbnail.png")
async def _audio_control_thumbnail_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if not client.current_track or not client.current_track.thumbnail:
        raise web.HTTPNotFound

    buffer = io.BytesIO()
    async with request.app.session.get(client.current_track.thumbnail) as response:
        if not response.ok:
            raise web.HTTPNotFound

        try:
            while data := await response.content.read(4096):
                buffer.write(data)
        except aiohttp.ClientPayloadError:
            raise web.HTTPInternalServerError

    return web.Response(body=buffer.read(), status=200)
