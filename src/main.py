"""
CLI entrypoint for Fruit Dealer Game.

Handles:
    - Building initial game data (fruits, cities, markets, player)
    - Rich-based rendering for main menu and simple in-game overview
    - Starting/loading games and persisting saves to disk

All money values are stored as cents (int) to avoid floating point issues.
"""

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List

from loguru import logger
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich import print

from models import Game, Player, City, Market, Fruit
from systems import PricingSystem
from game_engine import GameEngine


console = Console()

GAME_FILE = Path(__file__).resolve().parent / "game.json"


def _setup_data(player_name: str) -> Game:
    """
    Create initial game data for a fresh run.

    Builds fruits, cities with specialty modifiers, empty markets (prices filled
    by PricingSystem), and a starting player positioned in the first city with
    a default bankroll.

    Args:
        player_name: Name assigned to the new player.

    Returns:
        Game with populated fruits, cities, markets, player, and current day.
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

    # player + game
    player = Player(
        name=player_name, 
        money=2_000_00, 
        inventory={}, 
        current_city=cities[0]
        ) 

    return Game(fruits=fruits, cities=cities, player=player, markets=markets, current_day=1)

def start_new_game(player_name: str | None = None) -> GameEngine:
    """
    Launch a new game session and wrap it in a GameEngine.

    Prompts for player name when not provided to keep CLI usage simple.

    Args:
        player_name: Optional override to skip interactive prompt.

    Returns:
        Initialized GameEngine ready for play.
    """
    console.print("[bold green]Starting a new game[/bold green]")
    name = player_name or Prompt.ask("Player name")
    game = _setup_data(name)

    return GameEngine(game)

def _render_main_menu(console: Console) -> None:
    """
    Render the primary CLI menu with Rich formatting.

    Displays title/subtitle and three options: start, load, exit.
    """
    console.print()
    title = Text("🍉 Fruit Dealer Game 🍊", style="bold magenta")
    subtitle = Text("Trade smart. Travel far. Get rich.", style="dim")
    console.print(Align.center(title))
    console.print(Align.center(subtitle))
    console.print()

    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right", style="bold cyan")
    table.add_column(style="white")
    table.add_row("[1]", "Start a new game")
    table.add_row("[2]", "Load a game")
    table.add_row("[3]", "Exit")

    panel = Panel(
        Align.center(table),
        title="[bold green]Main Menu[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)

def _render_game_view(engine: GameEngine, console: Console) -> None:
    """
    Render a simple game overview with player, city, day, and market prices.

    Shows:
        - Player name, current city, and day
        - Player money (cents) and inventory summary
        - Current city's market prices (Market as single source of truth)
    """
    player = engine.player
    game = engine.game
    market = next((m for m in game.markets if m.city.name == player.current_city.name), None)

    header = Panel(
        Align.center(
            Text(
                f"{player.name} in {player.current_city.name} — Day {game.current_day}",
                style="bold yellow",
            )
        ),
        border_style="yellow",
        padding=(1, 2),
    )

    stats = Table.grid(padding=1)
    stats.add_column(style="cyan", justify="right")
    stats.add_column()
    stats.add_row("Money", f"{player.money}¢")
    stats.add_row("Inventory", ", ".join(f"{k} x{v}" for k, v in player.inventory.items()) or "empty")
    stats_panel = Panel(stats, title="[bold cyan]Player[/bold cyan]", border_style="cyan")

    prices_table = Table(title="Market Prices", header_style="bold green")
    prices_table.add_column("Fruit", style="magenta")
    prices_table.add_column("Price (¢)", justify="right", style="white")

    if market:
        for fruit_name, price in sorted(market.prices.items()):
            prices_table.add_row(fruit_name, str(price))
    else:
        prices_table.add_row("No market", "-")

    prices_panel = Panel(prices_table, border_style="green")

    console.print(header)
    console.print(stats_panel)
    console.print(prices_panel)

def _serialize_game(engine: GameEngine) -> Dict:
    """
    Convert the current game engine state into a JSON-friendly dict.

    Notes:
        - Markets are stored by city name with price mapping.
        - Player current city is stored by name for lookup on load.
        - Timestamp is informational.
    """
    player_city = engine.player.current_city.name
    city_lookup = {city.name: city for city in engine.game.cities}
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


def _deserialize_game(game_data: Dict) -> Game:
    """
    Rebuild a Game object from serialized JSON data.

    Expects the structure produced by _serialize_game; resolves city references
    by name when wiring markets and player location.
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


def store_game(game: GameEngine) -> None:
    """Persist the current game state to disk using GAME_FILE as target."""
    game_data = _serialize_game(game)
    with open(GAME_FILE, "w") as f:
        json.dump(game_data, f)
    logger.info(f"Game saved to '{GAME_FILE}'")


def load_game() -> GameEngine:
    """Load a saved game from disk and return a ready GameEngine."""
    with open(GAME_FILE, "r") as f:
        game_data = json.load(f)
    game = _deserialize_game(game_data)
    return GameEngine(game)
    

def cli():
    """
    Entry-point CLI that shows the main menu and routes the chosen action.

    Flow:
        1) Render Rich main menu
        2) Prompt for command (1-3)
        3) Start new game, load existing, or exit
        4) After start/load, render the game overview
    """
    logger.info("Starting Fruit Dealer Game")
    _render_main_menu(console)
    command = Prompt.ask("[bold blue]Enter a command (1-3):[/bold blue]")

    if command == "1":
        game = start_new_game()
        logger.info(
            f"Game created with player '{game.player.name}' at "
            f"'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'"
        )
        store_game(game)
        console.print(f"[bold green]Game saved to '{GAME_FILE}'[/bold green]")
        _render_game_view(game, console)
    elif command == "2":
        game = load_game()
        console.print(f"[bold green]Game loaded from '{GAME_FILE}'[/bold green]")
        _render_game_view(game, console)
    elif command == "3":
        exit()
    else:
        console.print("[bold red]Invalid command[/bold red]")


if __name__ == "__main__":
    cli()