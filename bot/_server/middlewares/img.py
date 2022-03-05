from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..core import middleware_group
if TYPE_CHECKING:
    from .._types import Handler, WebRequest


@middleware_group.middleware
@web.middleware
async def _img_middleware(request: WebRequest, handler: Handler) -> web.Response:
    await request.app.bot.image.wait_until_ready()
    return await handler(request)
