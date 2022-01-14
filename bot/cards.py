import io
import os
import random
from typing import ClassVar, Generic, Optional, List, Type, TypeVar, TYPE_CHECKING

from PIL import Image


CT = TypeVar("CT", bound="BaseCard")
SUITS = ("a", "b", "c", "d")
cardlist = [f for f in os.listdir(f"./bot/assets/cards")]


class BaseCard:

    __slots__ = ("id", "value", "suit")
    if TYPE_CHECKING:
        id: str
        value: int
        suit: int

    def __init__(self, filename: str) -> None:
        self.id = filename.removesuffix(".png")
        self.value = int(self.id[:-1])
        self.suit = SUITS.index(self.id[-1:])

    @property
    def image(self) -> Image:
        return Image.open(f"./bot/assets/cards/{self.id}.png")


class BaseHand(Generic[CT]):

    __slots__ = ("cards",)
    cardtype: ClassVar[Type[CT]] = BaseCard
    if TYPE_CHECKING:
        cards: List[CT]

    def __init__(self, cards: Optional[List[CT]] = None) -> None:
        if cards is not None:
            self.cards = cards
        else:
            self.cards = []

    @property
    def image(self) -> Image:
        n = len(self.cards)
        img = Image.new("RGBA", (80 * n, 100))
        for index, card in enumerate(self.cards):
            img.paste(card.image, (80 * index, 0, 80 * index + 80, 100))
        return img

    def make_image(self) -> io.BytesIO:
        _data = io.BytesIO()
        self.image.save(_data, format="PNG")
        _data.seek(0)
        return _data

    @property
    def value(self) -> int:
        return sum(card.value for card in self.cards)

    def draw(self) -> None:
        if len(self.cards) >= 52:
            raise ValueError("This hand cannot draw any more cards")

        random.shuffle(cardlist)
        for fcard in cardlist:
            if fcard.removesuffix(".png") not in [card.id for card in self.cards]:
                break

        self.cards.append(self.cardtype(fcard))


class PlayingCard(BaseCard):

    __slots__ = ("set",)
    if TYPE_CHECKING:
        set: bool

    def __init__(self, filename: str, set: bool = True) -> None:
        self.set = set
        super().__init__(filename)

    def flip(self) -> bool:
        self.set = not self.set
        return self.set
