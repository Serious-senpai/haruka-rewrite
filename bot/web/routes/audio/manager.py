from __future__ import annotations

import secrets
from typing import Union, overload, TYPE_CHECKING

import bidict

from lib.audio import MusicClient


__all__ = ("voice_manager",)


class _VoiceClientManager:

    __slots__ = ("mapping",)
    if TYPE_CHECKING:
        mapping: bidict.bidict[str, MusicClient]

    def __init__(self) -> None:
        self.mapping = {}

    def push(self, client: MusicClient) -> str:
        if client in self.mapping.values():
            return self.mapping.inverse[client]

        key = secrets.token_urlsafe()
        while key in self.mapping.keys():
            key = secrets.token_urlsafe()

        self.mapping[key] = client
        return key

    def pop(self, key: Union[str, MusicClient]) -> None:
        if isinstance(key, str):
            self.mapping.pop(key)
        else:
            self.mapping.inverse.pop(key)

    def check_pop(self, client: MusicClient) -> None:
        try:
            if not client.is_connected():
                self.pop(client)
        except KeyError:
            pass

    @overload
    def __getitem__(self, client: MusicClient) -> str:
        ...

    @overload
    def __getitem__(self, key: str) -> MusicClient:
        ...

    def __getitem__(self, client_or_key):
        if isinstance(client_or_key, str):
            self.check_pop(self.mapping[client_or_key])
            return self.mapping[client_or_key]
        elif isinstance(client_or_key, MusicClient):
            self.check_pop(client_or_key)
            return self.mapping.inverse[client_or_key]

    def __setitem__(self, key: str, value: MusicClient) -> None:
        self.mapping[key] = value


voice_manager = _VoiceClientManager()
