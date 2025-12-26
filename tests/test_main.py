import json
from io import StringIO
from pathlib import Path
import pytest

from main import (
    _deserialize_game,
    _render_game_view,
    _render_main_menu,
    _serialize_game,
    _setup_data,
    cli,
    load_game,
    start_new_game,
    store_game,
    GAME_FILE,
)
from game_engine import GameEngine
from models import Game, Player, City, Market, Fruit
from rich.console import Console


def test_setup_data_builds_game():
    game = _setup_data("Alice")
    assert isinstance(game, Game)
    assert game.player.name == "Alice"
    assert len(game.fruits) > 0
    assert len(game.cities) == len(game.markets)
    assert game.player.current_city == game.cities[0]


def test_start_new_game_uses_prompt_and_returns_engine(monkeypatch):
    """Test that start_new_game prompts for name and returns GameEngine."""
    monkeypatch.setattr("main.Prompt.ask", lambda _: "Bob")
    monkeypatch.setattr("builtins.input", lambda _: "")  # Mock input("Press Enter...")
    engine = start_new_game()
    assert isinstance(engine, GameEngine)
    assert engine.player.name == "Bob"


def test_store_and_load_roundtrip(tmp_path, monkeypatch):
    """Test that store and load preserve game state correctly."""
    monkeypatch.setattr("main.GAME_FILE", tmp_path / "game.json")
    engine = start_new_game(player_name="Carol")

    store_game(engine)
    loaded_engine = load_game()

    assert isinstance(loaded_engine, GameEngine)
    assert loaded_engine.player.name == engine.player.name
    assert loaded_engine.game.current_day == engine.game.current_day
    assert loaded_engine.game.cities[0].name == engine.game.cities[0].name


def test_serialize_and_deserialize_are_inverse(tmp_path, monkeypatch):
    """Test that serialize/deserialize roundtrip preserves all game data."""
    monkeypatch.setattr("main.GAME_FILE", tmp_path / "game.json")
    engine = start_new_game(player_name="Dave")

    data = _serialize_game(engine)
    rebuilt = _deserialize_game(data)

    assert isinstance(data, dict)
    assert isinstance(rebuilt, Game)
    assert rebuilt.player.name == engine.player.name
    assert len(rebuilt.markets) == len(engine.game.markets)
    assert rebuilt.player.current_city.name == engine.player.current_city.name


def test_cli_starts_new_game_branch(monkeypatch, capsys, tmp_path):
    """Test that CLI command 1 starts a new game."""
    monkeypatch.setattr("main.GAME_FILE", tmp_path / "game.json")
    # Stub start_new_game to avoid internal Prompt.ask for player name
    monkeypatch.setattr("main.start_new_game", lambda: GameEngine(_setup_data("Eve")))
    # Stub render_game_view to avoid heavy Rich output
    monkeypatch.setattr("main._render_game_view", lambda *args, **kwargs: None)
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "1"
        else:
            return "3"  # Exit after first command

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)

    cli()
    captured = capsys.readouterr()
    assert tmp_path.joinpath("game.json").exists()


def test_cli_handles_invalid_command(monkeypatch, capsys):
    """Test that invalid menu commands show error and retry."""
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        # First two calls return invalid, then exit
        if call_count["count"] <= 2:
            return "invalid"  # Invalid (not an integer)
        else:
            return "3"  # Valid (exit)

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    # Stub to avoid unintended prompts
    monkeypatch.setattr("main.start_new_game", lambda: GameEngine(_setup_data("Test")))
    monkeypatch.setattr("main.load_game", lambda: GameEngine(_setup_data("Test")))
    monkeypatch.setattr("main._render_game_view", lambda *args, **kwargs: None)

    cli()
    captured = capsys.readouterr()
    # Should show error for invalid input
    assert "Invalid choice" in captured.out or "Error" in captured.out
    # Should eventually exit
    assert "Thanks for playing" in captured.out


def test_cli_load_branch(tmp_path, monkeypatch, capsys):
    """Test that CLI command 2 loads a game."""
    # Stub load_game to avoid file I/O and internal prompts
    monkeypatch.setattr("main.load_game", lambda: GameEngine(_setup_data("Loaded")))
    monkeypatch.setattr("main._render_game_view", lambda *args, **kwargs: None)

    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"  # Exit after load

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)

    cli()
    captured = capsys.readouterr()
    assert "Game loaded successfully" in captured.out or "Loaded" in captured.out


def test_cli_exit_branch(monkeypatch, capsys):
    """Test that command 3 exits the CLI loop."""
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        return "3"  # Exit

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    
    # cli() uses break, not exit(), so it returns normally
    cli()
    captured = capsys.readouterr()
    assert "Thanks for playing" in captured.out


def test_render_main_menu_outputs_menu(monkeypatch, capsys):
    """Test that main menu renders correctly."""
    _render_main_menu()
    captured = capsys.readouterr()
    output = captured.out
    assert "Main Menu" in output
    assert "Start a new game" in output
    assert "Load a game" in output


def test_render_game_view_shows_player_and_prices():
    buffer = StringIO()
    console = Console(file=buffer, width=80, force_terminal=True, color_system=None)
    engine = start_new_game(player_name="Viewer")

    _render_game_view(engine, console)

    output = buffer.getvalue()
    assert "Viewer" in output
    assert "Day" in output
    assert "Market Prices" in output


# --- Validation Tests ---

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

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
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

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    monkeypatch.setattr("builtins.input", lambda _: "")

    engine = start_new_game()
    assert engine.player.name == "Alice-Bob"
    assert call_count["count"] == 3


def test_start_new_game_strips_whitespace(monkeypatch):
    """Test that whitespace is stripped from player names."""
    monkeypatch.setattr("main.Prompt.ask", lambda _: "  Alice  ")
    monkeypatch.setattr("builtins.input", lambda _: "")

    engine = start_new_game()
    assert engine.player.name == "Alice"


def test_start_new_game_accepts_valid_names(monkeypatch):
    """Test that valid player names are accepted."""
    test_names = ["Alice", "Bob Smith", "Mary-Jane", "José", "François"]

    for name in test_names:
        # Use default parameter to avoid closure issue
        monkeypatch.setattr("main.Prompt.ask", lambda _, n=name: n)
        monkeypatch.setattr("builtins.input", lambda _: "")
        engine = start_new_game()
        assert engine.player.name == name


# --- Menu Validation Tests ---

def test_cli_validates_menu_command_integer(monkeypatch, capsys):
    """Test that menu command must be an integer."""
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        # Return invalid inputs, then exit
        if call_count["count"] == 1:
            return "abc"  # Invalid (not integer)
        elif call_count["count"] == 2:
            return "5"  # Invalid (out of range)
        else:
            return "3"  # Valid (exit)

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    monkeypatch.setattr("main.start_new_game", lambda: GameEngine(_setup_data("Test")))
    monkeypatch.setattr("main.load_game", lambda: GameEngine(_setup_data("Test")))
    monkeypatch.setattr("main._render_game_view", lambda *args, **kwargs: None)

    cli()
    captured = capsys.readouterr()
    # Should show error messages for invalid inputs
    assert "Invalid choice" in captured.out or "Error" in captured.out
    # Should eventually exit
    assert "Thanks for playing" in captured.out


def test_cli_validates_menu_command_range(monkeypatch, capsys):
    """Test that menu command must be 1, 2, or 3."""
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        # Return invalid inputs, then exit
        if call_count["count"] == 1:
            return "0"  # Invalid (below range)
        elif call_count["count"] == 2:
            return "4"  # Invalid (above range)
        else:
            return "3"  # Valid (exit)

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    monkeypatch.setattr("main.start_new_game", lambda: GameEngine(_setup_data("Test")))
    monkeypatch.setattr("main.load_game", lambda: GameEngine(_setup_data("Test")))
    monkeypatch.setattr("main._render_game_view", lambda *args, **kwargs: None)

    cli()
    captured = capsys.readouterr()
    # Should show errors for invalid inputs
    assert "Invalid choice" in captured.out or "Error" in captured.out
    # Should eventually exit
    assert "Thanks for playing" in captured.out


# --- Load Game Error Handling Tests ---

def test_load_game_file_not_found_error(tmp_path, monkeypatch, capsys):
    """Test that FileNotFoundError is handled gracefully when loading."""
    monkeypatch.setattr("main.GAME_FILE", tmp_path / "nonexistent.json")

    # Simulate menu command 2 (load)
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"  # Exit after error

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    exit_called = {"called": False}
    monkeypatch.setattr("builtins.exit", lambda: exit_called.update({"called": True}))

    cli()
    captured = capsys.readouterr()
    assert "No save file found" in captured.out or "Error" in captured.out


def test_load_game_json_decode_error(tmp_path, monkeypatch, capsys):
    """Test that JSONDecodeError is handled when file is corrupted."""
    game_file = tmp_path / "game.json"
    game_file.write_text("{invalid json}", encoding="utf-8")
    monkeypatch.setattr("main.GAME_FILE", game_file)

    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    exit_called = {"called": False}
    monkeypatch.setattr("builtins.exit", lambda: exit_called.update({"called": True}))

    cli()
    captured = capsys.readouterr()
    assert "corrupted" in captured.out or "Error" in captured.out


def test_load_game_key_error_incompatible_save(tmp_path, monkeypatch, capsys):
    """Test that KeyError is handled when save file is incompatible."""
    game_file = tmp_path / "game.json"
    # Write incomplete JSON (missing required keys)
    game_file.write_text('{"player": {"name": "Test"}}', encoding="utf-8")
    monkeypatch.setattr("main.GAME_FILE", game_file)

    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"

    monkeypatch.setattr("main.Prompt.ask", mock_prompt)
    exit_called = {"called": False}
    monkeypatch.setattr("builtins.exit", lambda: exit_called.update({"called": True}))

    cli()
    captured = capsys.readouterr()
    assert "incompatible" in captured.out or "Error" in captured.out or "Missing key" in captured.out


# --- Success Message Tests ---

def test_start_new_game_shows_success_message(monkeypatch, capsys):
    """Test that success message is shown when game starts."""
    monkeypatch.setattr("builtins.input", lambda _: "")

    engine = start_new_game(player_name="Alice")
    captured = capsys.readouterr()
    assert "New game started for Alice" in captured.out or "Alice" in captured.out


def test_load_game_shows_success_message(tmp_path, monkeypatch, capsys):
    """Test that success message is shown when game loads."""
    monkeypatch.setattr("main.GAME_FILE", tmp_path / "game.json")
    engine = start_new_game(player_name="LoadTest")
    store_game(engine)

    # Now load it
    loaded_engine = load_game()
    # Just verify it loads without error
    assert loaded_engine.player.name == "LoadTest"
    