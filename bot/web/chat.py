from __future__ import annotations

import contextlib
import json
import secrets
from typing import Any, Dict, Optional, Type, Union, TYPE_CHECKING

import asyncpg
from aiohttp import web

if TYPE_CHECKING:
    import haruka
    from .server import WebRequest


authorized_sessions: Dict[str, UserSession] = {}


def action_json(action: str, **fields) -> Dict[str, Any]:
    return dict(action=action, **fields)


def error_json(message: str) -> Dict[str, str]:
    return action_json("ERROR", message=message)


async def http_authentication(request: WebRequest) -> str:
    username = request.headers.get("username")
    password = request.headers.get("password")
    if not username or not password:
        raise web.HTTPForbidden

    username = username.strip()
    password = password.strip()
    row = await request.app.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1 AND password = $2;", username, password)
    if row is None:
        raise web.HTTPForbidden

    return username


class UserSession:

    if TYPE_CHECKING:
        authorized: bool
        bot: haruka.Haruka
        pool: asyncpg.Pool
        request: WebRequest
        token: Optional[str]
        username: Optional[str]
        websocket: web.WebSocketResponse

    def __init__(self, *, request: WebRequest, websocket: web.WebSocketResponse) -> None:
        self.request = request
        self.websocket = websocket

        self.authorized = False
        self.bot = request.app.bot
        self.pool = request.app.bot.conn
        self.username = None
        self.token = None

    def authorize(self, username: str, *, token: Optional[str] = None) -> str:
        self.authorized = True
        self.username = username

        if not token:
            self.token = secrets.token_hex(16)
            while self.token in authorized_sessions:
                self.token = secrets.token_hex(16)
        else:
            self.token = token

        authorized_sessions[self.token] = self
        return self.token

    async def run(self) -> None:
        with contextlib.suppress(RuntimeError):
            if self.websocket.can_prepare(self.request):
                await self.websocket.prepare(self.request)

        async for message in self.websocket:
            try:
                data = message.json()
            except json.JSONDecodeError:
                await self.websocket.send_json(error_json("Invalid JSON data"))
            else:
                await self.process_message(data)

    @staticmethod
    def validate_json(data: Dict[str, Any], **required_fields: Union[Type[int], Type[str]]) -> bool:
        for field, data_type in required_fields.items():
            try:
                if not isinstance(data[field], data_type):
                    return False
            except KeyError:
                return False

        return True

    async def process_message(self, data: Dict[str, Any]) -> None:
        if not self.validate_json(data, action=str):
            return await self.websocket.send_json(error_json("Invalid JSON data"))

        action = data["action"].upper()
        if action == "REGISTER":
            valid = self.validate_json(data, username=str, password=str)
            if not valid:
                return await self.websocket.send_json(error_json("Invalid JSON data"))

            username = data["username"].strip()
            password = data["password"].strip()

            if len(username) < 3:
                return await self.websocket.send_json(error_json("Username must have at least 3 characters!"))

            if len(password) < 5:
                return await self.websocket.send_json(error_json("Password must have at least 5 characters!"))

            match = await self.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1", username)
            if match:
                return await self.websocket.send_json(error_json(f"Username \"{username}\" has already existed!"))
            else:
                await self.pool.execute("INSERT INTO chat_users (username, password) VALUES ($1, $2)", username, password)
                token = self.authorize(username)
                return await self.websocket.send_json(action_json("REGISTER_SUCCESS", session_token=token))

        elif action == "LOGIN":
            valid = self.validate_json(data, username=str, password=str)
            if not valid:
                return await self.websocket.send_json(error_json("Invalid JSON data"))

            username = data["username"].strip()
            password = data["password"].strip()

            match = await self.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1 AND password = $2;", username, password)
            if match is None:
                return await self.websocket.send_json(error_json("Invalid credentials"))

            token = self.authorize(username)
            return await self.websocket.send_json(action_json("LOGIN_SUCCESS", session_token=token))

        elif action == "RECONNECT":
            valid = self.validate_json(data, token=str)
            if not valid:
                return await self.websocket.send_json(error_json("Invalid JSON data"))

            token = data["token"]
            if token not in authorized_sessions:
                return await self.websocket.send_json(error_json("Invalid token"))

            session = authorized_sessions[token]
            if not session.websocket.closed:
                return await self.websocket.send_json(error_json("Invalid state"))

            self.authorize(session.username, token=token)
            return await self.websocket.send_json(action_json("RECONNECT_SUCCESS", session_token=token))

        else:
            return await self.websocket.send_json(error_json(f"Unrecognized action {action}"))
