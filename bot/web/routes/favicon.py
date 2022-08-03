from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/favicon.ico")
async def _favicon(request: WebRequest) -> web.Response:
    raise web.HTTPFound(request.app.bot.user.avatar.url)
