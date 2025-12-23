from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# type aliases
Money = int  # cents
Coordinates = Tuple[int, int]
Emoji = str


@dataclass
class Fruit:
    name: str
    base_price: Money
    emoji: Emoji
    description: str = field(default="No description provided")


@dataclass
class City:
    name: str
    position: Coordinates
    specialties: Dict[str, float]  # fruit -> price modifier


@dataclass
class Player:
    name: str
    money: Money
    inventory: Dict[str, int]
    current_city: City  # was: city

@dataclass
class Market:
    city: City
    prices: Dict[str, Money]  # fruit -> price


@dataclass
class Game:
    fruits: List[Fruit]
    cities: List[City]
    players: List[Player]  # was: player
    markets: List[Market]
    current_day: int  # was: day