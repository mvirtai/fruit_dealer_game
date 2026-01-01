from pathlib import Path
from typing import Dict, List
from typing import Callable
import pytest

from game_engine import GameEngine  
from models import Fruit, City, Market, Game, Money, Coordinates, Emoji, Player
from persistence import GAME_FILE

@pytest.fixture
def make_fruit() -> Callable[[str, Money, str], Fruit]:
    def _make_fruit(name: str, base_price: Money, emoji: Emoji, description: str) -> Fruit:
        return Fruit(name=name, base_price=base_price, emoji=emoji, description=description)
    return _make_fruit


@pytest.fixture
def make_city() -> Callable[[str, Coordinates, Dict[str, float]], City]:
    def _make_city(
        name: str,
        position: Coordinates,
        specialties: Dict[str, float] | None = None,
    ) -> City:
        # specialties describe per-fruit price modifiers for the city
        return City(
            name=name,
            position=position,
            specialties=specialties or {},
        )
    return _make_city

@pytest.fixture
def make_market() -> Callable[[City, Dict[str, Money]], Market]:
    def _make_market(city: City, prices: Dict[str, Money] = None) -> Market:
        return Market(city=city, prices=prices if prices else {})
    return _make_market


@pytest.fixture
def make_player() -> Callable[[str, Money, Dict[str, int], City | None], Player]:
    def _make_player(
        name: str,
        money: Money,
        inventory: Dict[str, int],
        current_city: City | None = None,
    ) -> Player:
        return Player(
            name=name,
            money=money,
            inventory=inventory,
            current_city=current_city if current_city else City("", (0, 0), {}),
        )
    return _make_player

@pytest.fixture
def make_game(make_market, make_player) -> Callable[[List[Fruit], List[City], dict], Game]:
    def _make_game(
        fruits: List[Fruit],
        cities: List[City],
        *,
        player_money: Money = 1000,
        player_inventory: Dict[str, int] | None = None,
        player_city: City | None = None,
    ) -> Game:
        # Create markets for each city; pricing system fills prices.
        markets = [make_market(city) for city in cities]
        player = make_player(
            name="Player",
            money=player_money,
            inventory=player_inventory or {},
            current_city=player_city or cities[0],
        )
        return Game(
            fruits=fruits,
            cities=cities,
            player=player,
            markets=markets,
            current_day=0,
        )
    return _make_game


# Fixtures
@pytest.fixture
def apple() -> Fruit:
    return Fruit(name="Apple", base_price=100, emoji="🍎", description="Fruit")

@pytest.fixture
def banana() -> Fruit:
    return Fruit(name="Banana", base_price=150, emoji="🍌", description="Fruit")

@pytest.fixture
def pori() -> City:
    return City(name="Pori", position=(0, 0), specialties={"Apple": 0.8})

@pytest.fixture
def helsinki() -> City:
    return City(name="Helsinki", position=(0, 0), specialties={"Apple": 1.2})


@pytest.fixture
def player_name() -> str:
    return "Test Player"

@pytest.fixture
def game_engine(make_game, apple, banana, pori) -> GameEngine:
    game = make_game(
        fruits=[apple, banana],
        cities=[pori],
        player_money=1_000,
        player_city=pori,
        player_inventory={},
    )
    return GameEngine(game)
