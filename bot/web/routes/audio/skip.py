from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

import discord
from aiohttp import web

from lib.audio import MusicClient
from .manager import voice_manager
from .utils import get_client
from ...core import routes
if TYPE_CHECKING:
    from ...server import WebRequest


@routes.get("/skip")
async def _skip_route(request: WebRequest) -> web.Response:
    client = get_client(request)
    if not client:
        raise web.HTTPBadRequest

    if client.is_connected():
        key = voice_manager[client]

        shuffle = client.shuffle
        target = client.target
        channel = client.channel

        with contextlib.suppress(discord.HTTPException):
            await target.send("Skipped due to a web request")

        await client.disconnect(force=True)
        new_client = await channel.connect(timeout=30.0, cls=MusicClient)
        new_client._shuffle = shuffle

        asyncio.create_task(new_client.play(target=target))
        voice_manager[key] = new_client

    return web.Response(status=204)
