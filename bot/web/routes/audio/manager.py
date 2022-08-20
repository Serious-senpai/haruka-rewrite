from __future__ import annotations

import secrets
from typing import Union, overload, TYPE_CHECKING

import bidict


__all__ = ("voice_manager",)


class _VoiceClientManager:

    __slots__ = ("mapping",)
    if TYPE_CHECKING:
        mapping: bidict.bidict[str, int]

    def __init__(self) -> None:
        self.mapping = bidict.bidict()

    def push(self, guild_id: int) -> str:
        if guild_id in self.mapping.values():
            return self.mapping.inverse[guild_id]

        key = secrets.token_urlsafe()
        while key in self.mapping.keys():
            key = secrets.token_urlsafe()

        self.mapping[key] = guild_id
        return key

    def pop(self, key: Union[str, int]) -> None:
        if isinstance(key, str):
            self.mapping.pop(key)
        elif isinstance(key, int):
            self.mapping.inverse.pop(key)
        else:
            raise TypeError(f"Unknown type {key.__class__.__name__}")

    @overload
    def __getitem__(self, guild_id: int) -> str:
        ...

    @overload
    def __getitem__(self, key: str) -> int:
        ...

    def __getitem__(self, key_or_id):
        if isinstance(key_or_id, str):
            return self.mapping[key_or_id]
        elif isinstance(key_or_id, int):
            return self.mapping.inverse[key_or_id]

    def __setitem__(self, key: str, guild_id: int) -> None:
        self.mapping[key] = guild_id


voice_manager = _VoiceClientManager()
