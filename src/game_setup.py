"""
Game initialization for Fruit Dealer Game.

Handles creating new games with initial data and player setup.
"""

import re

from rich.prompt import Prompt

from models import Game, Player, City, Market, Fruit
from game_engine import GameEngine
from ui import console, render_error, render_success


# Valid player name pattern: 2-20 chars, letters/spaces/hyphens
NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ \-]{2,20}$")


def setup_data(player_name: str) -> Game:
    """
    Create initial game data for a fresh run.

    Builds fruits, cities with specialty modifiers, empty markets (prices filled
    by PricingSystem), and a starting player positioned in the first city with
    a default bankroll.

    Args:
        player_name: Validated name assigned to the new player.

    Returns:
        Game: Populated with fruits, cities, markets, player, and current day.
    """
    fruits = [
        Fruit(name="Apple", base_price=100, emoji="🍎"),
        Fruit(name="Banana", base_price=80, emoji="🍌"),
        Fruit(name="Cherry", base_price=150, emoji="🍒"),
        Fruit(name="Grape", base_price=120, emoji="🍇"),
        Fruit(name="Orange", base_price=110, emoji="🍊"),
    ]

    cities = [
        City(name="Helsinki", position=(0, 0), specialties={"Apple": 1.1, "Banana": 1.0}),
        City(name="Tampere", position=(1, 2), specialties={"Cherry": 0.9, "Banana": 1.05}),
        City(name="Turku", position=(2, 1), specialties={"Orange": 0.8, "Grape": 1.2}),
        City(name="Oulu", position=(3, 3), specialties={"Banana": 0.95, "Apple": 1.15}),
        City(name="Pori", position=(0, 3), specialties={"Apple": 0.8, "Grape": 1.05}),
    ]

    markets = [Market(city=c, prices={}) for c in cities]

    player = Player(
        name=player_name,
        money=2_000_00,
        inventory={},
        current_city=cities[0],
    )

    return Game(fruits=fruits, cities=cities, player=player, markets=markets, current_day=1)


def start_new_game(player_name: str | None = None) -> GameEngine:
    """
    Launch a new game session and wrap it in a GameEngine.

    Prompts for player name when not provided to keep CLI usage simple.
    Validates name: 2-20 characters, letters/spaces/hyphens only.

    Args:
        player_name: Optional override to skip interactive prompt.

    Returns:
        Initialized GameEngine ready for play.
    """
    while True:
        if not player_name:
            console.print()
            player_name = Prompt.ask("[bold blue]Enter your player name[/bold blue]")
        player_name = player_name.strip()

        if NAME_PATTERN.match(player_name):
            break

        render_error(
            "Invalid player name.",
            hint="Use 2-20 letters (spaces and hyphens allowed).",
        )
        player_name = None

    game = setup_data(player_name)
    render_success(f"New game started for {player_name}!")

    return GameEngine(game)

