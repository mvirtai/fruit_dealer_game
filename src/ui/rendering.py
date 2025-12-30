"""
Rich-based UI rendering for Fruit Dealer Game.

All display functions for menus, game views, and feedback messages.
"""

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from game_engine import GameEngine


# Shared console instance
console = Console()


def render_error(msg: str, hint: str | None = None) -> None:
    """
    Display error message in a red-bordered Panel with optional hint.

    Args:
        msg: Main error message to display.
        hint: Optional hint text shown below the main message in dim style.
    """
    content = Text(msg, style="yellow")
    if hint:
        content.append(f"\n{hint}", style="dim")
    console.print()
    console.print(Panel(
        content,
        title="[bold yellow]Error[/bold yellow]",
        border_style="red",
        padding=(0, 2),
    ))


def render_success(msg: str) -> None:
    """
    Display success message in a green-bordered Panel.

    Args:
        msg: Success message to display.
    """
    console.print()
    console.print(Panel(
        Text(msg, style="bold green"),
        border_style="green",
        padding=(0, 2),
    ))


def render_main_menu() -> None:
    """
    Render the primary CLI menu with Rich formatting.

    Displays centered title/subtitle and a menu panel with three options:
    start new game, load existing game, and exit.
    """
    console.print()
    console.print()

    title = Text("🍉 Fruit Dealer Game 🍊", style="bold magenta")
    subtitle = Text("Trade smart. Travel far. Get rich.", style="dim italic")

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
        padding=(1, 4),
    )

    console.print(panel)
    console.print()


def render_game_view(engine: GameEngine) -> None:
    """
    Render game overview with player stats and market prices in horizontal layout.

    Displays:
        - Player stats panel (left): money, inventory, location, and day
        - Market prices panel (right): current city's fruit prices

    Args:
        engine: GameEngine containing current game state.
    """
    player = engine.player
    game = engine.game
    market = next((m for m in game.markets if m.city.name == player.current_city.name), None)

    player_dollars = player.money / 100
    dollars_formatted = f"${player_dollars:,.2f}"

    # Player stats table with location/day in footer
    stats = Table.grid(padding=1)
    stats.add_column(style="cyan", justify="right", width=12)
    stats.add_column(style="white")
    stats.add_row("Money", dollars_formatted)
    stats.add_row("Inventory", ", ".join(f"{k} x{v}" for k, v in player.inventory.items()) or "empty")
    
    # Footer with location and day
    stats.add_row("", "")
    stats.add_row(
        Text("📍 Location", style="dim"),
        Text(f"{player.current_city.name}", style="bold cyan"),
    )
    stats.add_row(
        Text("📅 Day", style="dim"),
        Text(f"{game.current_day}", style="bold cyan"),
    )

    stats_panel = Panel(
        stats,
        title=f"[bold cyan]{player.name}[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    # Prices table
    prices_table = Table(show_header=True, header_style="bold green")
    prices_table.add_column("Fruit", style="magenta", width=12)
    prices_table.add_column("Price ($)", justify="right", style="white")

    if market:
        for fruit_name, price in sorted(market.prices.items()):
            prices_table.add_row(fruit_name, f"${price / 100:,.2f}")
    else:
        prices_table.add_row("No market", "-")

    prices_panel = Panel(
        prices_table,
        title="[bold green]Market Prices[/bold green]",
        border_style="green",
        padding=(1, 2),
    )

    # Horizontal layout with spacing
    console.print()
    layout_table = Table.grid(padding=0, pad_edge=False)
    layout_table.add_column(ratio=1, min_width=6)
    layout_table.add_column(ratio=0)
    layout_table.add_column(ratio=2, min_width=10)
    layout_table.add_column(ratio=0)
    layout_table.add_column(ratio=1, min_width=6)
    
    layout_table.add_row("", stats_panel, "", prices_panel, "")
    
    console.print(layout_table)
    console.print()

