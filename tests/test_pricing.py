import pytest
from typing import Dict, List, Optional, Callable
from loguru import logger

from systems.pricing import PricingSystem
from models import Fruit, City, Game, Market, Money, Coordinates, Emoji
from conftest import make_game, make_fruit, make_city, make_market


@pytest.fixture
def apple() -> Fruit:
    return Fruit(name="Apple", base_price=100, emoji="🍎", description="Fruit")

@pytest.fixture
def pori() -> City:
    return City(name="Pori", position=(0, 0), specialties={"Apple": 0.8})

@pytest.fixture
def banana() -> Fruit:
    return Fruit(name="Banana", base_price=100, emoji="🍌", description="Fruit")

@pytest.fixture
def cherry() -> Fruit:
    return Fruit(name="Cherry", base_price=100, emoji="🍒", description="Fruit")

@pytest.fixture
def helsinki() -> City:
    return City(name="Helsinki", position=(0, 0), specialties={"Apple": 1.2})


def test_specialty_below_one_reduces_price(apple, pori, make_game):
    game = make_game(fruits=[apple], cities=[pori])
    pricing = PricingSystem(game)
    price = pricing.get_price("Apple", "Pori")
    logger.info(f"Price calculated: {price}")
    assert 64 <= price <= 96  # 100 * 0.8 * 0.8 = 64, 100 * 0.8 * 1.2 = 96

def test_specialty_above_one_increases_price(banana, helsinki, make_game):
    game = make_game(fruits=[banana], cities=[helsinki])
    pricing = PricingSystem(game)
    price = pricing.get_price("Banana", "Helsinki")
    logger.info(f"Price calculated: {price}")
    assert 96 <= price <= 144  # 100 * 1.2 * 0.8 .. 100 * 1.2 * 1.2

def test_neutral_specialty_keeps_base_range(banana, pori, make_game):
    pori.specialties["Banana"] = 1.0
    game = make_game(fruits=[banana], cities=[pori])
    pricing = PricingSystem(game)
    price = pricing.get_price("Banana", "Pori")
    logger.info(f"Price calculated: {price}")
    assert 80 <= price <= 120  # 100 * 1.0 * 0.8..1.2

def test_get_price_return_zero_for_unknown_fruit(apple, pori, make_game):
    game = make_game(fruits=[apple], cities=[pori])
    pricing = PricingSystem(game)
    price = pricing.get_price("Banana", "Pori")
    logger.info(f"Price calculated: {price}")
    assert price == 0


def test_get_price_return_zero_for_unknown_city(apple, pori, make_game):
    game = make_game(fruits=[apple], cities=[pori])
    pricing = PricingSystem(game)
    price = pricing.get_price("Apple", "Helsinki")
    logger.info(f"Price calculated: {price}")
    assert price == 0


def test_regenerate_prices_updates_all_markets(apple, pori, make_game, mocker):
    mock_uniform = mocker.patch('systems.pricing.random.uniform', side_effect=[0.9, 0.95])
    game = make_game(fruits=[apple], cities=[pori])
    pricing = PricingSystem(game)
    price_before = pricing.get_price("Apple", "Pori")
    pricing.regenerate_all_prices()
    price_after = pricing.get_price("Apple", "Pori")
    logger.info(f"Price before: {price_before}, Price after: {price_after}")
    assert price_before != price_after


def test_regenerate_updates_all_cities(apple, make_city, make_game):
    tokyo = make_city("Tokyo", (0, 0), {"Apple": 0.8})
    paris = make_city("Paris", (1, 1), {"Apple": 1.2})
    game = make_game(fruits=[apple], cities=[tokyo, paris])
    pricing = PricingSystem(game)
    assert pricing.get_price("Apple", "Tokyo") > 0
    assert pricing.get_price("Apple", "Paris") > 0
    logger.info(f"Price in Tokyo: {pricing.get_price('Apple', 'Tokyo')}")
    logger.info(f"Price in Paris: {pricing.get_price('Apple', 'Paris')}")
    assert pricing.get_price("Apple", "Tokyo") != pricing.get_price("Apple", "Paris")


def test_price_always_integer(make_fruit, make_city, make_game, mocker):
    mocker.patch('systems.pricing.random.uniform', return_value=0.833333)
    apple = make_fruit("Apple", 100, "🍎", "Fruit")
    city = make_city("Test", (0, 0), {"Apple": 0.9})
    game = make_game(fruits=[apple], cities=[city])
    
    pricing = PricingSystem(game)
    price = pricing.get_price("Apple", "Test")
    logger.info(f"Price calculated: {type(price)}, {price}")
    assert isinstance(price, int), "Price should always be an integer, as required by the Money type alias."


def test_empty_fruits_list_creates_empty_prices(make_city, make_game):
    city = make_city("Empty", (0, 0), {})
    game = make_game(fruits=[], cities=[city])
    pricing = PricingSystem(game)
    assert pricing.get_price("AnyFruit", "Empty") == 0, "Prices should be 0 for unknown fruits in empty game."

def test_unknown_fruit_returns_zero(apple, make_city, make_game):
    city = make_city("Known", (0, 0), {"Apple": 1.0})
    game = make_game(fruits=[apple], cities=[city])
    pricing = PricingSystem(game)
    assert pricing.get_price("UnknownFruit", "Known") == 0, "Prices should be 0 for unknown fruits in a known city."
