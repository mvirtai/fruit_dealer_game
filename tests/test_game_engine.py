from typing import List, Callable, Dict
from game_engine import GameEngine
from systems.pricing import PricingSystem
from models import Game, Fruit, City, Player, Market, Money
from conftest import make_game, apple, banana, pori, helsinki
import pytest
from loguru import logger


@pytest.mark.usefixtures("make_game", "apple", "banana", "pori", "helsinki")
class TestBuying:
    """Test suite for GameEngine buy() functionality."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, make_game, apple, banana, pori):
        """Set up test game with default player and inventory."""
        self.game = make_game(
            fruits=[apple, banana],
            cities=[pori],
            player_money=1000,
            player_city=pori,
            player_inventory={}
        )
        
    def test_buy_succeeds_with_funds(self):
        engine = GameEngine(self.game)
        initial_money = engine.player.money
        price = engine.pricing.get_price("Apple", "Pori")
        engine.buy("Apple", 1)
        assert engine.player.inventory["Apple"] == 1
        assert engine.player.money == initial_money - price

    def test_buy_raises_when_broke(self, apple, pori, make_game):
        game = make_game(
            fruits=[apple],
            cities=[pori],
            player_money=10,
            player_city=pori,
            player_inventory={}
        )
        engine = GameEngine(game)
        price = engine.pricing.get_price("Apple", "Pori")
        engine.player.money = price - 1
        with pytest.raises(ValueError, match="Not enough funds to buy 1 Apple"):
            engine.buy("Apple", 1)

    def test_buy_fruit_not_in_current_city(self):
        """Test that buying fails when player is in a city without a market."""
        engine = GameEngine(self.game)
        engine.player.current_city = City(name="Helsinki", position=(1, 1), specialties={})
        with pytest.raises(ValueError, match="No market for Helsinki"):
            engine.buy("Apple", 1)

    def test_buy_fruit_not_in_market(self, apple, pori, make_game):
        """Test that buying fails when fruit is not available in the market."""
        game = make_game(
            fruits=[apple],
            cities=[pori],
            player_money=1000,
            player_city=pori,
            player_inventory={},
        )
        engine = GameEngine(game)
        with pytest.raises(ValueError, match="Fruit not found in market: Banana"):
            engine.buy("Banana", 1)


    def test_buy_multiple_fruits(self):
        """Test buying multiple different fruits in sequence."""
        engine = GameEngine(self.game)
        init_funds = engine.player.money
        apple_price = engine.pricing.get_price("Apple", "Pori")
        banana_price = engine.pricing.get_price("Banana", "Pori")

        engine.buy("Apple", 1)
        engine.buy("Banana", 1)
        
        assert engine.player.inventory["Apple"] == 1
        assert engine.player.inventory["Banana"] == 1
        assert engine.player.money == (init_funds - (apple_price + banana_price))
        

class TestSelling:
    """Test suite for GameEngine sell() functionality."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, make_game, apple, banana, pori):
        """Set up test game with player having inventory to sell."""
        self.game = make_game(
            fruits=[apple, banana],
            cities=[pori],
            player_money=1000,
            player_city=pori,
            player_inventory={"Apple": 1, "Banana": 1}
        )
        self.engine = GameEngine(self.game)

    def test_sell_succeeds_with_inventory(self):
        """Test successful sale when player has sufficient inventory."""
        initial_money = self.engine.player.money
        apple_price = self.engine.pricing.get_price("Apple", "Pori")
        self.engine.sell("Apple", 1)
        
        assert self.engine.player.inventory["Apple"] == 0
        assert self.engine.player.money == (initial_money + apple_price)
        

    def test_sell_raises_when_not_enough_inventory(self):
        self.engine.player.inventory = {"Apple": 0}
        with pytest.raises(ValueError, match="Not enough Apple to sell 1"):
            self.engine.sell("Apple", 1)

    def test_sell_raises_when_not_in_market(self):
        with pytest.raises(ValueError, match="Fruit not found in market: Cherry"):
            self.engine.sell("Cherry", 1)

    def test_sell_multiple_fruits(self):
        """Test selling multiple different fruits in sequence."""
        initial_money = self.engine.player.money
        apple_price = self.engine.pricing.get_price("Apple", "Pori")
        banana_price = self.engine.pricing.get_price("Banana", "Pori")
        
        self.engine.sell("Apple", 1)
        self.engine.sell("Banana", 1)
        
        assert self.engine.player.inventory["Apple"] == 0
        assert self.engine.player.inventory["Banana"] == 0
        assert self.engine.player.money == (initial_money + apple_price + banana_price)


class TestTraveling:
    """Test suite for GameEngine travel() functionality."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, make_game, apple, banana, pori, helsinki):
        """Set up test game with multiple cities for travel testing."""
        self.game = make_game(
            fruits=[apple, banana],
            cities=[pori, helsinki],
            player_money=1000,
            player_city=pori,
            player_inventory={"Apple": 1, "Banana": 1}
        )
        self.engine = GameEngine(self.game)

    def test_travel_succeeds_with_valid_city(self):
        """Test successful travel to a valid city."""
        self.engine.travel("Helsinki")
        assert self.engine.player.current_city.name == "Helsinki"

    def test_travel_raises_when_invalid_city(self):
        with pytest.raises(ValueError, match="City not found: InvalidCity"):
            self.engine.travel("InvalidCity")
    
    def test_travel_raises_when_not_enough_funds(self):
        self.engine.player.money = 0
        with pytest.raises(ValueError, match=r"Not enough funds to travel to Helsinki\.\s+You need 50 more\."):
            self.engine.travel("Helsinki")