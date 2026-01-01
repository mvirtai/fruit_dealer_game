"""
Game state persistence for Fruit Dealer Game.

Handles saving and loading game state to/from JSON files.
All money values are stored as cents (int) to avoid floating point issues.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from loguru import logger

from models import Game, Player, City, Market, Fruit
from game_engine import GameEngine


# Default save file location
GAME_FILE = Path(__file__).resolve().parent / "game.json"


def serialize_game(engine: GameEngine) -> Dict:
    """
    Convert the current game engine state into a JSON-friendly dict.

    Notes:
        - Markets are stored by city name with price mapping.
        - Player current city is stored by name for lookup on load.
        - Timestamp is informational.

    Args:
        engine: GameEngine with current game state.

    Returns:
        Dict ready for JSON serialization.
    """
    player_city = engine.player.current_city.name
    return {
        "fruits": [asdict(fruit) for fruit in engine.game.fruits],
        "cities": [asdict(city) for city in engine.game.cities],
        "markets": [
            {"city": market.city.name, "prices": market.prices}
            for market in engine.game.markets
        ],
        "player": {
            "name": engine.player.name,
            "money": engine.player.money,
            "inventory": engine.player.inventory,
            "current_city": player_city,
        },
        "current_day": engine.game.current_day,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def deserialize_game(game_data: Dict) -> Game:
    """
    Rebuild a Game object from serialized JSON data.

    Expects the structure produced by serialize_game; resolves city references
    by name when wiring markets and player location.

    Args:
        game_data: Dict from JSON file.

    Returns:
        Reconstructed Game object.
    """
    fruits: List[Fruit] = [Fruit(**fruit) for fruit in game_data["fruits"]]
    cities: List[City] = [City(**city) for city in game_data["cities"]]
    city_lookup = {city.name: city for city in cities}

    markets = [
        Market(city=city_lookup[market["city"]], prices=market["prices"])
        for market in game_data["markets"]
    ]

    player_city = city_lookup[game_data["player"]["current_city"]]
    player = Player(
        name=game_data["player"]["name"],
        money=game_data["player"]["money"],
        inventory=game_data["player"]["inventory"],
        current_city=player_city,
    )

    return Game(
        fruits=fruits,
        cities=cities,
        player=player,
        markets=markets,
        current_day=game_data["current_day"],
    )


def store_game(engine: GameEngine, path: Path | None = None) -> None:
    """
    Persist the current game state to disk.

    Args:
        engine: GameEngine with current game state.
        path: Optional custom save path. Defaults to GAME_FILE.
    """
    save_path = path or GAME_FILE
    game_data = serialize_game(engine)
    with open(save_path, "w") as f:
        json.dump(game_data, f)
    logger.info(f"Game saved to '{save_path}'")


def load_game(path: Path | None = None) -> GameEngine:
    """
    Load a saved game from disk and return a ready GameEngine.

    Args:
        path: Optional custom load path. Defaults to GAME_FILE.

    Returns:
        GameEngine initialized with loaded game state.

    Raises:
        FileNotFoundError: If save file does not exist.
        json.JSONDecodeError: If save file contains invalid JSON.
        KeyError: If save file is missing required keys.
    """
    load_path = path or GAME_FILE
    with open(load_path, "r") as f:
        game_data = json.load(f)
    game = deserialize_game(game_data)
    return GameEngine(game)

