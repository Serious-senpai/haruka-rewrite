from __future__ import annotations

import asyncio
import contextlib
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

    await client.operable.wait()
    data = {
        "thumbnail": client.current_track.thumbnail,
        "title": client.current_track.title,
        "description": client.current_track.description,
    }
    return web.json_response(data)


@routes.get("/audio-control/status")
async def _audio_control_status_route(request: WebRequest) -> web.WebSocketResponse:
    websocket = web.WebSocketResponse()
    await websocket.prepare(request)

    client = get_client(request)
    if not client:
        await websocket.send_str("DISCONNECTED")
        await websocket.close()
        return websocket

    async def notify(websocket: web.WebSocketResponse, event: asyncio.Event) -> None:
        with contextlib.suppress(ConnectionResetError):
            await websocket.send_str("END")

        event.set()

    async def keep_alive(websocket: web.WebSocketResponse) -> None:
        while await asyncio.sleep(30, True) and not websocket.closed:
            with contextlib.suppress(ConnectionResetError):
                await websocket.send_bytes(b"")

    waiter = asyncio.Event()
    asyncio.create_task(keep_alive(websocket))
    while client.is_connected() and not websocket.closed:
        waiter.clear()
        await client.when_complete(notify(websocket, waiter))
        await waiter.wait()

    with contextlib.suppress(ConnectionResetError):
        await websocket.send_str("DISCONNECTED")

    await websocket.close()
    return websocket
