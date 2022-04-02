from __future__ import annotations

import re
from typing import TYPE_CHECKING

from aiohttp import web

from lib import pixiv
from ..core import middleware_group
if TYPE_CHECKING:
    from ..server import Handler, WebRequest


PIXIV_PATH_PATTERN = re.compile(r"/images/(\d{4,8}).png/?")


@middleware_group.middleware
@web.middleware
async def _pixiv_middleware(request: WebRequest, handler: Handler) -> web.Response:
    try:
        return await handler(request)
    except web.HTTPNotFound:
        match = PIXIV_PATH_PATTERN.fullmatch(request.path_qs)
        if match is not None:
            artwork_id = match.group(1)
            artwork = await pixiv.PixivArtwork.from_id(artwork_id, session=request.app.session)
            if not artwork:
                raise web.HTTPNotFound

            try:
                await artwork.stream(session=request.app.session)
                return await handler(request)
            except BaseException as exc:
                await request.app.report_error(exc)
                raise web.HTTPInternalServerError

        raise
