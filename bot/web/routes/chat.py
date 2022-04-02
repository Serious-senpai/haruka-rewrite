from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

import asyncpg
import discord
from aiohttp import web

from ..chat import (
    UserSession,
    action_json,
    authorized_websockets,
    http_authentication,
)
from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


def construct_message_json(row: asyncpg.Record) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "author": {"username": row["author"]},
        "content": row["content"],
        "time": row["time"].isoformat(),
    }


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

    try:
        start = int(request.query.get("start", "0"))  # Number of latest messages to skip
    except ValueError:
        raise web.HTTPBadRequest

    rows = await request.app.pool.fetch(
        """SELECT *
        FROM messages
        WHERE id <= (SELECT MAX(id) FROM messages) - $1
        ORDER BY id DESC
        LIMIT 50;
        """,
        start,
    )

    results = [construct_message_json(row) for row in rows]
    return web.json_response(results)


@routes.get("/chat/messages")
async def _chat_messages_get_endpoint(request: WebRequest) -> web.Response:
    try:
        message_id = int(request.query["id"])
    except (KeyError, ValueError):
        raise web.HTTPBadRequest

    await http_authentication(request)
    row = await request.app.pool.fetchrow("SELECT * FROM messages WHERE id = $1", message_id)
    if row is None:
        raise web.HTTPNotFound

    return web.json_response(construct_message_json(row))


@routes.delete("/chat/messages")
async def _chat_messages_delete_endpoint(request: WebRequest) -> web.Response:
    try:
        message_id = int(request.query["id"])
    except (KeyError, ValueError):
        raise web.HTTPBadRequest

    username = await http_authentication(request)
    row = await request.app.pool.fetchrow("SELECT * FROM messages WHERE id = $1", message_id)
    if row is None:
        raise web.HTTPNotFound

    if not row["author"] == username:
        raise web.HTTPForbidden

    await request.app.pool.execute("DELETE FROM messages WHERE id = $1", message_id)
    for ws in authorized_websockets:
        await ws.send_json(action_json("MESSAGE_DELETE", id=message_id))

    return web.Response(status=203)


@routes.post("/chat/messages")
async def _chat_messages_post_endpoint(request: WebRequest) -> web.Response:
    author = await http_authentication(request)
    try:
        data = await request.json()
        content = data["content"]
    except BaseException:
        raise web.HTTPBadRequest
    else:
        time = discord.utils.utcnow()
        row = await request.app.pool.fetchrow("INSERT INTO messages (author, content, time) VALUES ($1, $2, $3) RETURNING *;", author, content, time)

        # Construct JSON
        to_send = construct_message_json(row)

        for ws in authorized_websockets:
            await ws.send_json(action_json("MESSAGE_CREATE", **to_send))

        return web.Response(status=203)
