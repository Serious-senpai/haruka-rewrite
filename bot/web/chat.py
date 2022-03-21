from __future__ import annotations

import contextlib
import json
from typing import Any, Dict, Optional, Set, Tuple, TYPE_CHECKING

import asyncpg
from aiohttp import web

if TYPE_CHECKING:
    import haruka
    from .server import WebRequest


authorized_websockets: Set[web.WebSocketResponse] = set()


def action_json(action: str, **kwargs) -> Dict[str, Any]:
    return dict(action=action, **kwargs)


def error_json(message: str) -> Dict[str, str]:
    return action_json("ERROR", message=message)


def json_missing_field(field: str) -> Dict[str, str]:
    return error_json(f"Missing required field \"{field}\" in JSON data")


async def http_authentication(request: WebRequest) -> None:
    username = request.headers.get("username")
    password = request.headers.get("password")
    if not username or not password:
        raise web.HTTPForbidden

    row = await request.app.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1 AND password = $2;", username, password)
    if row is None:
        raise web.HTTPForbidden


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
                await self.websocket.send_json(error_json("Invalid JSON data"))
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

            if not isinstance(username, str) or not isinstance(password, str):
                return await self.websocket.send_json(error_json("Invalid data type"))

            if len(username) < 3:
                return await self.websocket.send_json(error_json("Username must have at least 3 characters!"))

            if len(password) < 5:
                return await self.websocket.send_json(error_json("Password must have at least 5 characters!"))

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

            if not isinstance(username, str) or not isinstance(password, str):
                return await self.websocket.send_json(error_json("Invalid credentials"))

            match = await self.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1 AND password = $2;", username, password)
            if match is None:
                return await self.websocket.send_json(error_json("Invalid credentials"))

            self.authorize(username)
            return await self.websocket.send_json(action_json("LOGIN_SUCCESS"))

        if action == "HEARTBEAT":
            return

        return await self.websocket.send_json(error_json(f"Unrecognized action {action}"))
