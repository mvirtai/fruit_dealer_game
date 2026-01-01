"""
Tests for persistence module.

Tests serializing and deserializing, storing and loading game.
"""
import pytest
from datetime import datetime
from loguru import logger
import json

from game_engine import GameEngine
from persistence import serialize_game, deserialize_game, store_game, load_game
from conftest import make_game, apple, banana, pori, helsinki
from models import Fruit, City, Game


def test_serialize_game_engine_state_into_json_friendly_dict(make_game, apple, banana, pori, helsinki):
    # Arrange
    game = make_game(
        fruits=[
            Fruit(name="Apple", base_price=10, emoji="🍎", description="A round and tasteful fruit"),
            Fruit(name="Banana", base_price=20, emoji="🍌", description="A tropical, yellow fruit")
        ],
        cities=[
            City(name="Pori", position=(0, 0), specialties={"Apple": 0.8}),
            City(name="Helsinki", position=(1, 1), specialties={"Banana": 1.2})
        ],
        player_inventory={
            "Apple": 10,
            "Banana": 50
        })
    engine = GameEngine(game)

    # Act
    result = serialize_game(engine)
    logger.info(result)

    # Assert
    # result
    assert len(result) == 6
    assert isinstance(result, dict) is True
    assert "created_at" in result
    assert isinstance(result["created_at"], str)
    
    # fruits
    fruits = result["fruits"]
    assert len(fruits) == 2

    apple, banana = fruits[0], fruits[1]
    assert apple["name"] == "Apple"
    assert apple["base_price"] == 10
    assert apple["emoji"] == "🍎"
    assert apple["description"] == "A round and tasteful fruit"

    assert banana["name"] == "Banana"
    assert banana["base_price"] == 20
    assert banana["emoji"] == "🍌"
    assert banana["description"] == "A tropical, yellow fruit"

    assert len(result["markets"]) == 2
    pori_market, helsinki_market = result["markets"][0], result["markets"][1]
    
    assert pori_market["city"] == "Pori"
    assert "prices" in pori_market
    assert isinstance(pori_market["prices"], dict)
    assert "Apple" in pori_market["prices"]
    assert "Banana" in pori_market["prices"]
    assert isinstance(pori_market["prices"]["Apple"], int)

    assert helsinki_market["city"] == "Helsinki"
    assert "prices" in helsinki_market
    assert isinstance(helsinki_market["prices"], dict)
    assert "Apple" in helsinki_market["prices"]
    assert "Banana" in helsinki_market["prices"]
    assert isinstance(helsinki_market["prices"]["Banana"], int)

    # Player is created with default values 
    assert "player" in result
    player = result["player"]
    assert player["name"] == "Player"
    assert player["money"] == 1000
    assert isinstance(player["inventory"], dict)
    assert player["inventory"] == {
        "Apple": 10,
        "Banana": 50
    }
    assert player["current_city"] == "Pori"

    assert result["current_day"] == 0


def test_deserialize_game_reconstructs_game_from_dict():
    # Arrange 
    game_data = {
        "fruits": [
            {"name": "Apple", "base_price": 100, "emoji": "🍎", "description": "Tasty"}
        ],
        "cities": [
            {"name": "Pori", "position": [0, 0], "specialties": {"Apple": 0.8}}
        ],
        "markets": [
            {"city": "Pori", "prices": {"Apple": 80}}
        ],
        "player": {
            "name": "TestPlayer",
            "money": 5000,
            "inventory": {"Apple": 10},
            "current_city": "Pori"
        },
        "current_day": 3,
        "created_at": "2025-12-31 12:00:00" 
    }

    # Act
    result = deserialize_game(game_data)

    # Assert
    assert isinstance(result, Game)
    assert len(result.fruits) == 1
    assert result.fruits[0].name == "Apple"
    assert result.fruits[0].base_price == 100
    assert result.fruits[0].emoji == "🍎"
    assert result.fruits[0].description == "Tasty"

    assert len(result.cities) == 1
    assert result.cities[0].name == "Pori"
    assert result.cities[0].position == [0, 0]
    assert result.cities[0].specialties.get("Apple") == 0.8

    assert len(result.markets) == 1
    assert result.markets[0].city.name == "Pori"
    assert result.markets[0].prices.get("Apple") == 80

    assert result.player.name == "TestPlayer"
    assert result.player.money == 5000
    assert result.player.inventory.get("Apple") == 10
    assert result.player.current_city.name == "Pori"

    assert result.current_day == 3


def test_store_game_writes_to_file(tmp_path, make_game):
    # Arrange
    save_file = tmp_path / "test_save.json"
    game = make_game(
        fruits=[
            Fruit(name="Apple", base_price=10, emoji="🍎", description="A round and tasteful fruit"),
            Fruit(name="Banana", base_price=20, emoji="🍌", description="A tropical, yellow fruit")
        ],
        cities=[
            City(name="Pori", position=(0, 0), specialties={"Apple": 0.8}),
            City(name="Helsinki", position=(1, 1), specialties={"Banana": 1.2})
        ],
        player_inventory={
            "Apple": 10,
            "Banana": 50
        })
    engine = GameEngine(game)

    # Act
    store_game(engine, path=save_file)

    # Assert
    assert save_file.exists()
    content = save_file.read_text()
    assert "fruits" in content


def test_load_game_reads_from_file(tmp_path):
    # Arrange
    save_file = tmp_path / "test_save.json"
    game_data = {
        "fruits": [
            {"name": "Apple", "base_price": 100, "emoji": "🍎", "description": "Tasty"}
        ],
        "cities": [
            {"name": "Pori", "position": [0, 0], "specialties": {"Apple": 0.8}}
        ],
        "markets": [
            {"city": "Pori", "prices": {"Apple": 80}}
        ],
        "player": {
            "name": "TestPlayer",
            "money": 5000,
            "inventory": {"Apple": 10},
            "current_city": "Pori"
        },
        "current_day": 3,
        "created_at": "2025-12-31 12:00:00" 
    }
    save_file.write_text(json.dumps(game_data))

    # Act
    engine = load_game(path=save_file)

    # Assert
    assert isinstance(engine, GameEngine)
    assert engine.game.fruits[0].name == "Apple"


def test_store_and_load_round_trip(tmp_path, make_game):
    # Arrange
    save_file = tmp_path / "round_trip.json"
    game = make_game(
        fruits=[
            Fruit(name="Apple", base_price=10, emoji="🍎", description="A round and tasteful fruit"),
            Fruit(name="Banana", base_price=20, emoji="🍌", description="A tropical, yellow fruit")
        ],
        cities=[
            City(name="Pori", position=(0, 0), specialties={"Apple": 0.8}),
            City(name="Helsinki", position=(1, 1), specialties={"Banana": 1.2})
        ],
        player_inventory={
            "Apple": 10,
            "Banana": 50
        })
    engine = GameEngine(game)
    original_player_money = engine.player.money
    
    # Act
    store_game(engine, path=save_file)
    loaded_engine = load_game(path=save_file)
    
    # Assert
    assert loaded_engine.player.money == original_player_money
    assert loaded_engine.game.fruits[0].name == engine.game.fruits[0].name


def test_load_game_raises_when_file_not_found(tmp_path):
    missing_file = tmp_path / "nonexistent.json"
    
    with pytest.raises(FileNotFoundError):
        load_game(path=missing_file)