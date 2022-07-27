from __future__ import annotations

from typing import TYPE_CHECKING

from .artwork import PixivArtwork


__all__ = ("NSFWArtworkDetected",)


class NSFWArtworkDetected(Exception):
    """Exception raised when a NSFW artwork is detected from a given ID"""

    __slots__ = ("artwork",)
    if TYPE_CHECKING:
        artwork: PixivArtwork

    def __init__(self, artwork: PixivArtwork) -> None:
        self.artwork = artwork
        super().__init__(f"NSFW artwork with ID {artwork.id}")
