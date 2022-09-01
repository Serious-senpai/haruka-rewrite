from __future__ import annotations

import functools
import io
import os
import random
import re
from typing import Any, Generic, Optional, List, Literal, Tuple, Type, TypeVar, TYPE_CHECKING

from PIL import Image


CardValue = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
CardSuit = Literal[0, 1, 2, 3]


SUITS = ("a", "b", "c", "d")
CARD_FILE_PATTERN = re.compile(r"(\d{1,2})([abcd])\.png")
cardlist = [f for f in os.listdir(f"./bot/assets/cards") if CARD_FILE_PATTERN.fullmatch(f) is not None]


def extract_card_info(filename: str) -> Tuple[CardValue, CardSuit]:
    match = CARD_FILE_PATTERN.fullmatch(filename)
    if match is None:
        raise ValueError(f"Invalid card file {filename}")

    return int(match.group(1)), ord(match.group(2)) - ord("a")


@functools.total_ordering
class BaseCard:

    __slots__ = ("filename", "value", "suit")
    if TYPE_CHECKING:
        filename: str
        value: CardValue
        suit: CardSuit

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.value, self.suit = extract_card_info(filename)

    def to_image(self) -> Image.Image:
        return Image.open(f"./bot/assets/cards/{self.filename}")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseCard):
            return NotImplemented

        return (self.value, self.suit) == (other.value, other.suit)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, BaseCard):
            return NotImplemented

        return (self.value, self.suit) < (other.value, other.suit)

    @classmethod
    def copy(cls: Type[T], card: T) -> T:
        return cls(card.filename)


T = TypeVar("T", bound=BaseCard)


class PlayingCard(BaseCard):

    __slots__ = ("up",)
    if TYPE_CHECKING:
        up: bool

    def __init__(self, filename: str, up: bool = True) -> None:
        super().__init__(filename)
        self.up = up

    def flip(self) -> bool:
        self.up = not self.up
        return self.up

    def to_image(self) -> Image.Image:
        if self.up:
            return super().to_image()

        return Image.open("./bot/assets/misc/card_sleeve.png")


class CardHand(Generic[T]):

    __slots__ = ("hand",)
    if TYPE_CHECKING:
        hand: List[T]

    def __init__(self, cards: Optional[List[T]] = None) -> None:
        if cards is not None:
            self.hand = cards
        else:
            self.hand = []

    @property
    def cards_count(self) -> int:
        return len(self.hand)

    def sort(self) -> None:
        self.hand.sort()

    def to_image(self) -> Image.Image:
        image = Image.new("RGBA", (80 * self.cards_count, 100))
        for index, card in enumerate(self.hand):
            image.paste(card.to_image(), (80 * index, 0, 80 * index + 80, 100))

        return image

    def to_image_data(self) -> io.BytesIO:
        data = io.BytesIO()
        self.to_image().save(data, format="PNG")
        data.seek(0)
        return data

    @property
    def value(self) -> int:
        return sum(card.value for card in self.hand)

    @property
    def streak(self) -> int:
        existed = [False] * 16
        for card in self.hand:
            existed[card.value] = True
            if card.value == 1:
                # Treat A as both 1 and 14
                existed[14] = True

        assert not existed[0] and not existed[-1]
        longest = current = 0
        for state in existed:
            if state:
                current += 1
            else:
                longest = max(longest, current)
                current = 0

        return longest

    def draw(self, cls: Type[T], *, count: int = 1) -> None:
        if self.cards_count >= 52:
            raise ValueError("This hand cannot draw any more cards")

        random.shuffle(cardlist)
        existed = set(card.filename for card in self.hand)

        counter = 0
        for fcard in cardlist:
            if fcard not in existed:
                # This is unnecessary since we will not iterate over this card again
                #
                # existed.add(fcard)
                self.hand.append(cls(fcard))
                counter += 1
                if counter == count:
                    return
