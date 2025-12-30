"""
Command parsing and execution for Fruit Dealer Game.

Handles the game loop, command parsing, and command execution.
"""

from rich.prompt import Prompt

from game_engine import GameEngine
from persistence import store_game
from ui import console, render_error, render_success, render_game_view


# Available commands
COMMANDS = {"help", "buy", "sell", "travel", "status", "save", "quit", "exit"}


def pluralize(word: str, count: int) -> str:
    """Return singular or plural form based on count."""
    return word if count == 1 else word + "s"


def parse_command(cmd: str) -> tuple[str, list[str]] | None:
    """
    Parse user command into (command, args) tuple.

    Examples:
        "help" -> ("help", [])
        "buy apple 5" -> ("buy", ["apple", "5"])
        "travel Tampere" -> ("travel", ["Tampere"])

    Args:
        cmd: Raw command string from user.

    Returns:
        (command, args) tuple or None if command is invalid.
    """
    if not cmd:
        return None

    parts = cmd.strip().split()
    if not parts:
        return None

    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    if command not in COMMANDS:
        render_error(
            "Invalid command",
            hint="Try typing 'help' to see available commands."
        )
        return None

    return (command, args)


def execute_command(engine: GameEngine, command: str, args: list[str]) -> bool:
    """
    Execute a parsed command.

    Args:
        engine: GameEngine with current game state.
        command: Parsed command name.
        args: Command arguments.

    Returns:
        True to continue game loop, False to exit to main menu.
    """
    if command == "help":
        # TODO: render_help_menu()
        return True

    if command == "status":
        # Game view is rendered at the start of each loop
        return True

    if command == "save":
        store_game(engine)
        render_success("Game saved!")
        return True

    if command in ("quit", "exit"):
        return False

    # Commands with args
    if command == "buy":
        if len(args) != 2:
            render_error("Usage: buy <fruit> <quantity>", hint="Example: buy apple 5")
            return True

        fruit, qty_str = args
        if not qty_str.isdigit():
            render_error("Quantity must be a number", hint="Example: buy apple 5")
            return True

        try:
            qty = int(qty_str)
            engine.buy(fruit.capitalize(), qty)
            render_success(f"Bought {qty} {pluralize(fruit, qty)}!")
        except ValueError as e:
            render_error(str(e))
        return True

    if command == "sell":
        if len(args) != 2:
            render_error("Usage: sell <fruit> <quantity>", hint="Example: sell banana 3")
            return True

        fruit, qty_str = args
        if not qty_str.isdigit():
            render_error("Quantity must be a number", hint="Example: sell banana 3")
            return True

        try:
            qty = int(qty_str)
            engine.sell(fruit.capitalize(), qty)
            render_success(f"Sold {qty} {pluralize(fruit, qty)}!")
        except ValueError as e:
            render_error(str(e))
        return True

    if command == "travel":
        if len(args) != 1:
            render_error("Usage: travel <city>", hint="Example: travel Tampere")
            return True

        try:
            engine.travel(args[0].capitalize())
            render_success(f"Traveled to {args[0].capitalize()}!")
        except ValueError as e:
            render_error(str(e))
        return True

    return True  # Unknown command - continue


def game_loop(engine: GameEngine) -> None:
    """
    Main game loop. Renders view, accepts commands, updates state.

    Returns when player enters 'quit' or 'exit'.

    Args:
        engine: GameEngine with current game state.
    """
    while True:
        render_game_view(engine)

        raw_cmd = Prompt.ask("[bold blue]Command[/bold blue]")

        parsed = parse_command(raw_cmd)
        if parsed is None:
            continue

        command, args = parsed

        should_continue = execute_command(engine, command, args)

        if not should_continue:
            return

