from __future__ import annotations

import contextlib
import json
import secrets
from typing import Any, Dict, Optional, Type, Union, TYPE_CHECKING

import asyncpg
from aiohttp import web

if TYPE_CHECKING:
    import haruka
    from .app import WebApp
    from .server import WebRequest


authorized_sessions: Dict[str, UserSession] = {}


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

    __slots__ = (
        "app",
        "authorized",
        "bot",
        "pool",
        "request",
        "session_token",
        "username",
        "websocket",
    )
    if TYPE_CHECKING:
        app: WebApp
        authorized: bool
        bot: haruka.Haruka
        pool: asyncpg.Pool
        request: WebRequest
        session_token: Optional[str]
        username: Optional[str]
        websocket: web.WebSocketResponse

    def __init__(self, *, request: WebRequest, websocket: web.WebSocketResponse) -> None:
        self.request = request
        self.websocket = websocket

        self.authorized = False
        self.app = request.app
        self.bot = request.app.bot
        self.pool = request.app.bot.conn
        self.username = None
        self.session_token = None

    def authorize(self, username: str, *, session_token: Optional[str] = None) -> str:
        self.authorized = True
        self.username = username

        if not session_token:
            self.session_token = secrets.token_hex(16)
            while self.session_token in authorized_sessions:
                self.session_token = secrets.token_hex(16)
        else:
            self.session_token = session_token

        authorized_sessions[self.session_token] = self
        return self.session_token

    async def run(self) -> None:
        with contextlib.suppress(RuntimeError):
            if self.websocket.can_prepare(self.request):
                await self.websocket.prepare(self.request)

        async for message in self.websocket:
            try:
                data = message.json()
            except json.JSONDecodeError:
                await self.send_error("Invalid JSON data")
            else:
                await self.process_message(data)

    async def send_action(self, action: str, **fields) -> None:
        if "token" in fields and fields["token"] is None:
            del fields["token"]

        action = action.upper()
        try:
            return await self.websocket.send_json(dict(action=action, **fields))
        except ConnectionError:
            pass
        except BaseException as exc:
            await self.app.report_error(exc)

    async def send_error(self, message: str, **fields) -> None:
        return await self.send_action("ERROR", message=message, **fields)

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
        token = data.get("token")
        if not self.validate_json(data, action=str):
            return await self.send_error("Invalid JSON data", token=token)

        action = data["action"].upper()
        if action == "REGISTER":
            valid = self.validate_json(data, username=str, password=str)
            if not valid:
                return await self.send_error("Invalid JSON data", token=token)

            username = data["username"].strip()
            password = data["password"].strip()

            if len(username) < 3:
                return await self.send_error("Username must have at least 3 characters!", token=token)

            if len(password) < 5:
                return await self.send_error("Password must have at least 5 characters!", token=token)

            match = await self.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1", username)
            if match:
                return await self.send_error(f"Username \"{username}\" has already existed!", token=token)
            else:
                await self.pool.execute("INSERT INTO chat_users (username, password) VALUES ($1, $2)", username, password)
                session_token = self.authorize(username)
                return await self.send_action("REGISTER_SUCCESS", session_token=session_token, token=token)

        elif action == "LOGIN":
            valid = self.validate_json(data, username=str, password=str)
            if not valid:
                return await self.send_error("Invalid JSON data")

            username = data["username"].strip()
            password = data["password"].strip()

            match = await self.pool.fetchrow("SELECT * FROM chat_users WHERE username = $1 AND password = $2;", username, password)
            if match is None:
                return await self.send_error("Invalid credentials", token=token)

            session_token = self.authorize(username)
            return await self.send_action("LOGIN_SUCCESS", session_token=session_token, token=token)

        elif action == "RECONNECT":
            valid = self.validate_json(data, session_token=str)
            if not valid:
                return await self.send_error("Invalid JSON data", token=token)

            session_token = data["session_token"]
            if session_token not in authorized_sessions:
                return await self.send_error("Invalid session token", token=token)

            session = authorized_sessions[session_token]
            if not session.websocket.closed:
                return await self.send_error("Old session is still active", token=token)

            self.authorize(session.username, token=token)
            return await self.send_action("RECONNECT_SUCCESS", session_token=session_token, token=token)

        else:
            return await self.send_error(f"Unrecognized action {action}", token=token)
