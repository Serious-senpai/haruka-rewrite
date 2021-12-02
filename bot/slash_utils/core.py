from typing import Any, Callable, Dict, List, Optional

import discord

from .converter import (
    ChannelConverter,
    RoleConverter,
    UserConverter,
)
from .types import (
    CommandOptionPayload,
)


__all__ = (
    "parse",
)


PARAMS_MAPPING: Dict[int, Callable[[discord.Interaction, str], Any]] = {
    6: UserConverter,
    7: ChannelConverter,
    8: RoleConverter,
}


def parse(interaction: discord.Interaction) -> Dict[str, Any]:
    ret: Dict[str, Any] = {}

    try:
        options: List[CommandOptionPayload] = interaction.data["options"]
    except KeyError:
        return ret

    for option in options:
        key: str = option["name"]
        converter: Optional[Callable[[discord.Interaction, str], Any]] = PARAMS_MAPPING.get(option["type"])

        value: Any
        if converter:
            value = converter(interaction, option["value"])
        else:
            value = option["value"]

        ret[key] = value

    return ret