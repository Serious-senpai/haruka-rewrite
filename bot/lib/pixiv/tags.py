from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING


__all__ = ("PixivArtworkTag",)


class PixivArtworkTag:

    __slots__ = (
        "name",
        "locked",
        "deletable",
        "romaji",
        "_translations",
    )
    if TYPE_CHECKING:
        name: str
        locked: bool
        deletable: bool
        romaji: Optional[str]
        _translations: Dict[str, str]

    def __init__(self, data: Dict[str, Any]) -> None:
        self.name = data["tag"]
        self.locked = data["locked"]
        self.deletable = data["deletable"]
        self.romaji = data.get("romaji")
        self._translations = data.get("translation", {})

    def translate(self, language: str = "en") -> Optional[str]:
        return self._translations.get(language)

    @property
    def url(self) -> str:
        return f"https://www.pixiv.net/en/tags/{self.name}/artworks"

    def __str__(self) -> str:
        return self.translate() or self.name

    def __repr__(self) -> str:
        return f"<PixivArtworkTag name={self.name} translations={list(self._translations.keys())}>"
