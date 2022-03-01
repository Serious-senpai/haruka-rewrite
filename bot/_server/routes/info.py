from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..types import WebRequest


@routes.get("/info")
async def _info_route(request: WebRequest) -> web.Response:
    bot = request.app.bot
    to_send = {
        "Username": str(bot.user),
        "User ID": bot.user.id,
        "Owner": str(bot.owner),
        "Servers": len(bot.guilds),
    }
    await web.json_response(to_send)
