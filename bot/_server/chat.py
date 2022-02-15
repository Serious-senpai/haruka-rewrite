from __future__ import annotations

import contextlib
import json
from typing import Any, Dict, Optional, Set, Tuple, TYPE_CHECKING

import asyncpg
import discord
from aiohttp import web

if TYPE_CHECKING:
    import haruka
    from .types import WebRequest


def error_json(message: str) -> Dict[str, str]:
    return {"action": "ERROR", "message": message}


def json_decode_error() -> Dict[str, str]:
    return error_json("Invalid JSON data")


def json_missing_field(field: str) -> Dict[str, str]:
    return error_json(f"Missing required field \"{field}\" in JSON data")


def action_json(action: str, **kwargs) -> Dict[str, Any]:
    return dict(action=action, **kwargs)


authorized_websockets: Set[web.WebSocketResponse] = set()


class UserSession:

    if TYPE_CHECKING:
        authorized: bool
        bot: haruka.Haruka
        pool: asyncpg.Pool
        request: WebRequest
        username: Optional[str]
        websocket: web.WebSocketResponse

    def __init__(self, *, request: WebRequest, websocket: web.WebSocketResponse) -> None:
        self.request = request
        self.websocket = websocket

        self.authorized = False
        self.bot = request.app.bot
        self.pool = request.app.bot.conn
        self.username = None

    def authorize(self, username: str) -> None:
        self.authorized = True
        self.username = username
        authorized_websockets.add(self.websocket)

    def __del__(self) -> None:
        with contextlib.suppress(KeyError):
            authorized_websockets.remove(self.websocket)

    async def run(self) -> None:
        with contextlib.suppress(RuntimeError):
            if self.websocket.can_prepare(self.request):
                await self.websocket.prepare()

        async for message in self.websocket:
            try:
                data = message.json()
            except json.JSONDecodeError:
                await self.websocket.send_json(json_decode_error())
            else:
                await self.process_message(data)

    def check_json_field(self, data: Dict[str, Any], *fields: Tuple[str]) -> Optional[str]:
        for field in fields:
            if field not in data:
                return field

    async def process_message(self, data: Dict[str, Any]) -> None:
        if self.check_json_field(data, "action"):
            return await self.websocket.send_json(json_missing_field("action"))

        action = data["action"]
        if action == "REGISTER":
            missing_key = self.check_json_field(data, "username", "password")
            if missing_key is not None:
                return await self.websocket.send_json(json_missing_field(missing_key))

            username = data["username"]
            password = data["password"]

            match = await self.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1", username)
            if match:
                return await self.websocket.send_json(error_json(f"Username \"{username}\" has already existed!"))
            else:
                await self.pool.execute("INSERT INTO chat_users (username, password) VALUES ($1, $2)", username, password)
                self.authorize(username)
                return await self.websocket.send_json(action_json("REGISTER_SUCCESS"))

        if action == "LOGIN":
            missing_key = self.check_json_field(data, "username", "password")
            if missing_key is not None:
                return await self.websocket.send_json(json_missing_field(missing_key))

            username = data["username"]
            password = data["password"]

            match = await self.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1", username)
            if not match:
                return await self.websocket.send_json(error_json("Invalid credentials"))

            if password == match["password"]:
                self.authorize(username)
                return await self.websocket.send_json(action_json("LOGIN_SUCCESS"))
            else:
                return await self.websocket.send_json(error_json("Invalid credentials"))

        if action == "MESSAGE_CREATE":
            if not self.authorized:
                return await self.websocket.send_json(error_json("Please login or register first to create a message"))

            missing_key = self.check_json_field(data, "username", "content")
            if missing_key is not None:
                return await self.websocket.send_json(json_missing_field(missing_key))

            username = self.username
            content = data["content"]
            time = discord.utils.utcnow()

            await self.pool.execute("INSERT INTO messages (author, content, time) VALUES $1, $2, $3", username, content, time)
            for ws in authorized_websockets:
                await ws.send_json(action_json("MESSAGE_CREATE", username=username, content=content, time=time))

        return await self.websocket.send_json(error_json(f"Unrecognized action {action}"))
