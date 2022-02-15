from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import routes
if TYPE_CHECKING:
    from ..types import WebRequest


@routes.get("/")
async def _main_page(request: WebRequest) -> web.Response:
    return web.Response(
        text=request.app.index,
        status=200,
        content_type="text/html",
    )
