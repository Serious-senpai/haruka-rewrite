from __future__ import annotations

import asyncio
import contextlib
import json
from typing import TYPE_CHECKING

import discord
from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..types import WebRequest


chat_websockets = []


@routes.get("/chat")
async def _chat_ws_endpoint(request: WebRequest) -> web.WebSocketResponse:
    websocket = web.WebSocketResponse()
    authenticate = False
    await websocket.prepare(request)

    async for ws_message in websocket:
        try:
            data = json.loads(ws_message.data)
        except json.JSONDecodeError:
            await websocket.send_json({"action": "ERROR", "message": "invalid JSON data"})
        else:
            if data["action"] == "REGISTER":
                username = data.get("username", "")
                password = data.get("password", "")

                if len(username) < 3:
                    await websocket.send_json({"action": "REGISTER_ERROR", "message": "Username must have at least 3 characters!"})
                    continue

                match = await request.app.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1", username)
                if match:
                    await websocket.send_json({"action": "REGISTER_ERROR", "message": "This username has already existed!"})
                else:
                    await request.app.pool.execute("INSERT INTO chat_users VALUES ($1, $2)", username, password)
                    await websocket.send_json({"action": "REGISTER_SUCCESS", "message": "Successfully registered!"})
                    authenticate = True
                    chat_websockets.append(websocket)

            elif data["action"] == "LOGIN":
                username = data.get("username", "")
                password = data.get("password", "")
                match = await request.app.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1", username)
                if not match:
                    await websocket.send_json({"action": "LOGIN_ERROR", "message": "Invalid credentials"})
                else:
                    correct_password = match["password"]
                    if password == correct_password:
                        await websocket.send_json({"action": "LOGIN_SUCCESS", "message": "Successfully logged in!"})
                        authenticate = True
                        chat_websockets.append(websocket)
                    else:
                        await websocket.send_json({"action": "LOGIN_ERROR", "message": "Invalid credentials"})

            elif authenticate:
                if data["action"] == "MESSAGE":
                    author = data["author"]
                    content = data["content"]
                    time = discord.utils.utcnow()
                    await request.app.pool.execute("INSERT INTO messages (author, content, time) VALUES ($1, $2, $3)", author, content, time)
                    await asyncio.gather(*[ws.send_json({"action": "MESSAGE", "author": author, "content": content, "time": time}) for ws in chat_websockets])

            else:
                await websocket.send_json({"action": "ERROR", "message": "Unauthorized websocket connection"})

    with contextlib.suppress(ValueError):
        chat_websockets.remove(websocket)

    return websocket
