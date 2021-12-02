from typing import TypedDict, Union


class CommandOptionPayload(TypedDict):
    name: str
    value: Union[bool, float, int, str]
    type: int
