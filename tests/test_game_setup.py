"""
Tests for game_setup module.

Tests game initialization, player name validation, and new game creation.
"""
import pytest

from game_setup import setup_data, start_new_game
from game_engine import GameEngine
from models import Game


def test_setup_data_builds_game():
    """Test that setup_data creates a valid game."""
    game = setup_data("Alice")
    assert isinstance(game, Game)
    assert game.player.name == "Alice"
    assert len(game.fruits) > 0
    assert len(game.cities) == len(game.markets)
    assert game.player.current_city == game.cities[0]


def test_start_new_game_uses_prompt_and_returns_engine(monkeypatch):
    """Test that start_new_game prompts for name and returns GameEngine."""
    monkeypatch.setattr("game_setup.Prompt.ask", lambda _: "Bob")
    monkeypatch.setattr("builtins.input", lambda _: "")  # Mock input("Press Enter...")
    engine = start_new_game()
    assert isinstance(engine, GameEngine)
    assert engine.player.name == "Bob"


def test_start_new_game_validates_player_name_length(monkeypatch, capsys):
    """Test that player names must be 2-20 characters."""
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "A"  # Too short
        elif call_count["count"] == 2:
            return "A" * 21  # Too long
        else:
            return "Alice"  # Valid

    monkeypatch.setattr("game_setup.Prompt.ask", mock_prompt)
    monkeypatch.setattr("builtins.input", lambda _: "")  # Mock input("Press Enter...")

    engine = start_new_game()
    assert engine.player.name == "Alice"
    assert call_count["count"] == 3  # Two invalid attempts, then valid


def test_start_new_game_validates_player_name_characters(monkeypatch):
    """Test that player names only allow letters, spaces, and hyphens."""
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "Alice123"  # Numbers not allowed
        elif call_count["count"] == 2:
            return "Alice@Bob"  # Special chars not allowed
        else:
            return "Alice-Bob"  # Valid (hyphen allowed)

    monkeypatch.setattr("game_setup.Prompt.ask", mock_prompt)
    monkeypatch.setattr("builtins.input", lambda _: "")

    engine = start_new_game()
    assert engine.player.name == "Alice-Bob"
    assert call_count["count"] == 3


def test_start_new_game_strips_whitespace(monkeypatch):
    """Test that whitespace is stripped from player names."""
    monkeypatch.setattr("game_setup.Prompt.ask", lambda _: "  Alice  ")
    monkeypatch.setattr("builtins.input", lambda _: "")

    engine = start_new_game()
    assert engine.player.name == "Alice"


def test_start_new_game_accepts_valid_names(monkeypatch):
    """Test that valid player names are accepted."""
    test_names = ["Alice", "Bob Smith", "Mary-Jane", "José", "François"]

    for name in test_names:
        # Use default parameter to avoid closure issue
        monkeypatch.setattr("game_setup.Prompt.ask", lambda _, n=name: n)
        monkeypatch.setattr("builtins.input", lambda _: "")
        engine = start_new_game()
        assert engine.player.name == name


def test_start_new_game_shows_success_message(monkeypatch, capsys):
    """Test that success message is shown when game starts."""
    monkeypatch.setattr("builtins.input", lambda _: "")

    engine = start_new_game(player_name="Alice")
    captured = capsys.readouterr()
    assert "New game started for Alice" in captured.out or "Alice" in captured.out

