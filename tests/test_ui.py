"""
Tests for ui module.

Tests user interface rendering functions.
"""
import pytest
from io import StringIO
from rich.console import Console

from ui import render_main_menu, render_game_view
from game_setup import start_new_game


def test_render_main_menu_outputs_menu(monkeypatch, capsys):
    """Test that main menu renders correctly."""
    render_main_menu()
    captured = capsys.readouterr()
    output = captured.out
    assert "Main Menu" in output
    assert "Start a new game" in output
    assert "Load a game" in output


def test_render_game_view_shows_player_and_prices(capsys):
    """Test that game view shows player information and prices."""
    buffer = StringIO()
    test_console = Console(file=buffer, width=80, force_terminal=True, color_system=None)
    engine = start_new_game(player_name="Viewer")

    # Use monkeypatch to temporarily replace the console
    import ui.rendering as rendering_module
    original_console = rendering_module.console
    rendering_module.console = test_console
    
    try:
        render_game_view(engine)
        output = buffer.getvalue()
        assert "Viewer" in output
        assert "Day" in output
        assert "Market Prices" in output
    finally:
        rendering_module.console = original_console

