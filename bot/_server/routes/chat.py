from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..chat import UserSession, http_authentication
from ..core import routes
if TYPE_CHECKING:
    from ..types import WebRequest


@routes.get("/chat")
async def _chat_ws_endpoint(request: WebRequest) -> web.WebSocketResponse:
    websocket = web.WebSocketResponse()
    await websocket.prepare(request)

    session = UserSession(request=request, websocket=websocket)
    await session.run()

    return websocket


@routes.get("/chat/history")
async def _chat_history_endpoint(request: WebRequest) -> web.Response:
    await http_authentication(request)
    rows = await request.app.pool.fetch("SELECT * FROM messages ORDER BY id DESC LIMIT 50;")
    results = [dict(id=row["id"], author=row["author"], content=row["content"], time=row["time"].isoformat()) for row in rows]
    return web.json_response(results)


@routes.get("/chat/message")
async def _chat_message_endpoint(request: WebRequest) -> web.Response:
    try:
        message_id = request.query.get("id")
        message_id = int(message_id)
    except ValueError:
        raise web.HTTPBadRequest

    await http_authentication(request)
    row = await request.app.pool.fetchrow("SELECT * FROM messages WHERE id = $1", message_id)
    if row is None:
        raise web.HTTPNotFound

    return web.json_response(id=row["id"], author=row["author"], content=row["content"], time=row["time"].isoformat())
