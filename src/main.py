from loguru import logger
from rich.console import Console
from rich.prompt import Prompt
from rich import print
from datetime import datetime
import json

from models import Game, Player, City, Market, Fruit
from systems import PricingSystem
from game_engine import GameEngine


console = Console()


def _setup_data(player_name: str) -> Game:
    # data setup
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

def start_new_game() -> GameEngine:
    console.print("[bold green]Starting a new game[/bold green]")
    player_name = Prompt.ask("Player name")
    game = _setup_data(player_name)

    return GameEngine(game)


def store_game(game: GameEngine) -> None:
    with open("game.json", "w") as f:
        json.dump(game.to_dict(), f)
    logger.info(f"Game saved to 'game.json'")


def cli():
    logger.info("Starting Fruit Dealer Game")
    console.print("[bold green]Welcome to the Fruit Dealer Game[/bold green]")
    console.print("[bold]1. Start a new game[/bold]")
    console.print("[bold]2. Load a game[/bold]")
    console.print("[bold]3. Exit[/bold]")
    command = Prompt.ask("[bold blue]Enter a command:[/bold blue]")

    if command == "1":
        game = start_new_game()
        logger.info(f"Game created with player '{game.player.name}' at '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'")
        store_game(game)
    elif command == "2":
        pass
    elif command == "3":
        exit()
    else:
        console.print("[bold red]Invalid command[/bold red]")


if __name__ == "__main__":
    cli()