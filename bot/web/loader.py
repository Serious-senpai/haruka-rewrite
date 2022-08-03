from typing import Dict, TYPE_CHECKING


class TextFileLoader:

    if TYPE_CHECKING:
        data: Dict[str, str]

    def __init__(self) -> None:
        self.data = {}

    def open(self, path: str) -> str:
        try:
            return self.data[path]
        except KeyError:
            with open(path, "r", encoding="utf-8") as f:
                self.data[path] = f.read()

            return self.data[path]

    def clear(self) -> None:
        self.data.clear()
