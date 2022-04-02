__all__ = ("AudioNotFound",)


class AudioNotFound(Exception):

    __slots__ = ("track_id",)

    def __init__(self, track_id: str) -> None:
        self.track_id = track_id
        super().__init__(f"The local audio file for track ID {track_id} can't be found")
