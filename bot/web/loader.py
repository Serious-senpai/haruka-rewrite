from typing import Dict, TYPE_CHECKING


class TextFileLoader:

    __slots__ = ("_data",)
    if TYPE_CHECKING:
        _data: Dict[str, str]

    def __init__(self) -> None:
        self._data = {}

    def open(self, path: str) -> str:
        try:
            return self._data[path]
        except KeyError:
            with open(path, "r", encoding="utf-8") as f:
                self._data[path] = f.read()

            return self._data[path]

    def clear(self) -> None:
        self._data.clear()
