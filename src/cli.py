"""
CLI entrypoint for Fruit Dealer Game.

Handles main menu rendering and routing to game actions.
"""

import json

from loguru import logger
from rich.prompt import Prompt

from commands import game_loop
from game_setup import start_new_game
from persistence import store_game, load_game, GAME_FILE
from ui import console, render_error, render_success, render_main_menu, render_game_view


def cli() -> None:
    """
    Entry-point CLI that shows the main menu and routes the chosen action.

    Main loop flow:
        1) Render Rich main menu
        2) Validate menu command input (1-3 only, retry on invalid)
        3) Execute command: start new game, load existing, or exit
        4) After start/load, enter game loop
        5) Return to menu after each action (except exit)

    Menu commands:
        - 1: Start new game (validates player name, saves to disk)
        - 2: Load game (handles FileNotFoundError, JSONDecodeError, KeyError)
        - 3: Exit application
    """
    logger.info("Starting Fruit Dealer Game")

    while True:
        render_main_menu()

        # Validate menu input
        while True:
            try:
                cmd = int(Prompt.ask("[bold blue]Enter a command (1-3)[/bold blue]"))
                if cmd not in (1, 2, 3):
                    raise ValueError
                break
            except ValueError:
                render_error("Invalid choice.", hint="Enter 1, 2, or 3.")

        # Handle menu actions
        if cmd == 1:
            engine = start_new_game()
            store_game(engine)
            game_loop(engine)

        elif cmd == 2:
            try:
                engine = load_game()
                render_success("Game loaded successfully!")
                game_loop(engine)
            except FileNotFoundError:
                render_error("No save file found.", hint=f"Expected: {GAME_FILE}")
            except json.JSONDecodeError:
                render_error("Save file is corrupted.", hint="Start a new game.")
            except KeyError as e:
                render_error(
                    "Save file is incompatible.",
                    hint=f"Missing key: {e}. Start a new game.",
                )

        elif cmd == 3:
            console.print()
            console.print("[dim]Thanks for playing! 👋[/dim]")
            break


if __name__ == "__main__":
    cli()
