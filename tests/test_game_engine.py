from typing import List, Callable
from game_engine import GameEngine
from models import Game, Fruit, City, Player, Market, Money, Coordinates, Emoji


import pytest

@pytest.fixture
def make_game(make_market) -> Callable[[List[Fruit], List[City]], Game]:
    def _make_game(fruits: List[Fruit], cities: List[City]) -> Game:
        markets = [make_market(city) for city in cities]
        # Create dummy player for pricing tests (player not used by PricingSystem)
        dummy_city = cities[0] if cities else City("Dummy", (0, 0), {})
        dummy_player = Player(
            name="TestPlayer",
            money=10000,
            inventory={},
            city=dummy_city
        )
        return Game(
            fruits=fruits,
            cities=cities,
            player=dummy_player,
            markets=markets,
            day=0
        )
    return _make_game