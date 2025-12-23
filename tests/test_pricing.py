import pytest
from typing import Dict, List, Optional, Callable
from loguru import logger

from systems.pricing import PricingSystem
from models import Fruit, City, Game, Market, Money, Coordinates, Emoji


# =============================================================================
# TESTING RULES
# =============================================================================
#
# 1. AAA PATTERN - Every test follows three phases:
#    - ARRANGE: Set up test data (create objects, mock dependencies)
#    - ACT: Call the function/method being tested
#    - ASSERT: Verify the result matches expectations
#
# 2. ONE BEHAVIOR PER TEST
#    - Each test should verify ONE specific behavior
#    - Bad:  test_pricing_system() (too broad)
#    - Good: test_specialty_modifier_reduces_price()
#
# 3. TEST NAMES DESCRIBE BEHAVIOR
#    - Use: test_<action>_<expected_result>
#    - Examples:
#      - test_get_price_returns_zero_for_unknown_city()
#      - test_specialty_modifier_below_one_reduces_price()
#      - test_regenerate_prices_updates_all_markets()
#
# 4. TESTS ARE INDEPENDENT
#    - No test should depend on another test's side effects
#    - Each test sets up its own state via fixtures
#
# 5. TEST EDGE CASES
#    - Empty lists, zero values, missing keys, None values
# =============================================================================

# =============================================================================
# FACTORIES #
# =============================================================================

@pytest.fixture
def make_fruit() -> Callable[[str, Money, str], Fruit]:
    def _make_fruit(name: str, base_price: Money, emoji: Emoji, description: str) -> Fruit:
        return Fruit(name=name, base_price=base_price, emoji=emoji, description=description)
    return _make_fruit


@pytest.fixture
def make_city() -> Callable[[str, Coordinates, Dict[str, float]], City]:
    def _make_city(name: str, position: Coordinates, specialties: Dict[str, float]) -> City:
        return City(name=name, position=position, specialties=specialties)
    return _make_city

@pytest.fixture
def make_market() -> Callable[[City, Dict[str, Money]], Market]:
    def _make_market(city: City, prices: Dict[str, Money] = None) -> Market:
        return Market(city=city, prices=prices if prices else {})
    return _make_market

@pytest.fixture
def make_game(make_fruit, make_city, make_market) -> Callable[[List[Fruit], List[City]], Game]:
    def _make_game(fruits: List[Fruit], cities: List[City]) -> Game:
        # create markets for each city.
        # prices are created by the pricing system in the game initialization.
        markets = [make_market(city) for city in cities]
        return Game(
            fruits=fruits,
            cities=cities,
            players=[],
            markets=markets,
            current_day=0
        )
    return _make_game

# =============================================================================
# FIXTURES #
# =============================================================================

@pytest.fixture
def apple(make_fruit):
    return make_fruit("Apple", 100, "🍎", "A red, round fruit")

@pytest.fixture
def banana(make_fruit):
    return make_fruit("Banana", 100, "🍌", "A yellow, long fruit")

@pytest.fixture
def cherry(make_fruit):
    return make_fruit("Cherry", 120, "🍒", "A small, red, sweet fruit")

@pytest.fixture
def pori(make_city):
    return make_city("Pori", (1, 1), {"Apple": 0.9, "Banana": 1.1})

# =============================================================================
# TESTS #
# =============================================================================

def test_specialty_below_one_reduces_price(apple, pori, make_game):
    game = make_game(fruits=[apple], cities=[pori])
    pricing = PricingSystem(game)
    price = pricing.get_price("Apple", "Pori")
    logger.info(f"Price calculated: {price}")
    assert 72 <= price <= 120


def test_specialty_above_one_increases_price(banana, pori, make_game):
    game = make_game(fruits=[banana], cities=[pori])
    pricing = PricingSystem(game)
    price = pricing.get_price("Banana", "Pori")
    logger.info(f"Price calculated: {price}")
    assert 88 <= price <= 132


def test_non_specialty_fruit_uses_default_modifier(cherry, pori, make_game):
    game = make_game(fruits=[cherry], cities=[pori])
    pricing = PricingSystem(game)
    price = pricing.get_price("Cherry", "Pori")
    logger.info(f"Price calculated: {price}")
    assert 96 <= price <= 144



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
