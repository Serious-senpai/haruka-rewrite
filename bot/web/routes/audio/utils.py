from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .manager import voice_manager
if TYPE_CHECKING:
    from ...server import WebRequest
    from lib.audio import MusicClient


def get_key(request: WebRequest) -> Optional[str]:
    return request.query.get("key")


def get_client(request: WebRequest) -> Optional[MusicClient]:
    try:
        key = get_key(request)
        return voice_manager[key]
    except KeyError:
        return
