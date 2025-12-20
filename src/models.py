from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from dataclasses import field



# type aliases
Money = int # cents
Coordinates = Tuple[int, int]


@dataclass
class Fruit:
    name: str 
    base_price: Money
    emoji: str
    description: Optional[str] = None


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
    current_city: City


@dataclass
class Market:
    city: City
    prices: Dict[str, Money] # fruit -> price


@dataclass
class Game:
    fruits: List[Fruit]
    cities: List[City]
    players: List[Player]
    markets: List[Market]
    current_day: int
