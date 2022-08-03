from __future__ import annotations

import asyncio
import os
from typing import Optional, TYPE_CHECKING

from aiohttp import web

import env
from lib import pixiv
from ..core import routes
if TYPE_CHECKING:
    from ..server import WebRequest


@routes.get("/pixiv-user")
async def _pixiv_user_route(request: WebRequest) -> web.Response:
    try:
        url = request.query["url"]
    except KeyError:
        raise web.HTTPBadRequest

    match = pixiv.USER_PATTERN.fullmatch(url)
    if not match:
        raise web.HTTPBadRequest

    user_id = int(match.group(2))
    if os.path.exists(f"./server/images/{user_id}.zip"):
        raise web.HTTPTemporaryRedirect(env.HOST + "/images/" + f"{user_id}.zip")

    artworks = await pixiv.PixivArtwork.from_user(user_id, session=request.app.session)
    if not artworks:
        return web.Response(status=204)

    async def save(index: int) -> Optional[int]:
        artwork = await artworks.get(index)
        if artwork is not None:
            status = await artwork.save(pixiv.ImageType.ORIGINAL, session=request.app.session)
            if status:
                return artwork.id

    artwork_ids = await asyncio.gather(*[save(index) for index in len(artworks)])

    args = ["zip", f"./server/images/{user_id}.zip"]
    args.extend(f"./server/images/{artwork_id}.png" for artwork_id in artwork_ids if artwork_id is not None)
    process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    _, _stderr = await process.communicate()

    if _stderr:
        request.app.log(f"Cannot zip artworks from user ID {user_id}. stderr: " + _stderr.decode("utf-8"))
        await request.app.bot.report(f"Cannot zip artworks from user ID `{user_id}` at the server side. This is the report.", send_state=False)
        raise web.HTTPInternalServerError
    else:
        raise web.HTTPTemporaryRedirect(env.HOST + "/images/" + f"{user_id}.zip")
