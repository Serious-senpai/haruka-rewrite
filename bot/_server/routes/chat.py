from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..chat import UserSession
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
