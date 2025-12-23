from dataclasses import dataclass
from typing import Dict, Tuple, List
from dataclasses import field



# type aliases
Money = int # cents
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
    specialties: Dict[str, float] # fruit -> price modifier (0.0 to 1.0)


@dataclass
class Player:
    name: str
    money: Money
    inventory: Dict[str, int]
    city: City


@dataclass
class Market:
    city: City
    prices: Dict[str, Money] # fruit -> price


@dataclass
class Game:
    fruits: List[Fruit]    # Multiple fruits to trade
    cities: List[City]     # Multiple cities to visit
    player: Player         # Single player
    markets: List[Market]  # One market per city
    day: int
