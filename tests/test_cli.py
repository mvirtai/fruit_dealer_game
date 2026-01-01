"""
Tests for cli module.

Tests command-line interface, menu handling, validation, and error handling.
"""
import pytest

from cli import cli
from game_setup import setup_data
from game_engine import GameEngine


def test_cli_starts_new_game_branch(monkeypatch, capsys, tmp_path):
    """Test that CLI command 1 starts a new game."""
    monkeypatch.setattr("persistence.GAME_FILE", tmp_path / "game.json")
    monkeypatch.setattr("cli.GAME_FILE", tmp_path / "game.json")
    # Stub start_new_game to avoid internal Prompt.ask for player name
    monkeypatch.setattr("cli.start_new_game", lambda: GameEngine(setup_data("Eve")))
    # Stub game_loop to avoid heavy Rich output
    monkeypatch.setattr("cli.game_loop", lambda engine: None)
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "1"
        else:
            return "3"  # Exit after first command

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)

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

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)
    # Stub to avoid unintended prompts
    monkeypatch.setattr("cli.start_new_game", lambda: GameEngine(setup_data("Test")))
    monkeypatch.setattr("cli.load_game", lambda: GameEngine(setup_data("Test")))
    monkeypatch.setattr("cli.game_loop", lambda engine: None)

    cli()
    captured = capsys.readouterr()
    # Should show error for invalid input
    assert "Invalid choice" in captured.out or "Error" in captured.out
    # Should eventually exit
    assert "Thanks for playing" in captured.out


def test_cli_load_branch(tmp_path, monkeypatch, capsys):
    """Test that CLI command 2 loads a game."""
    # Stub load_game to avoid file I/O and internal prompts
    monkeypatch.setattr("cli.load_game", lambda: GameEngine(setup_data("Loaded")))
    monkeypatch.setattr("cli.game_loop", lambda engine: None)

    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"  # Exit after load

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)

    cli()
    captured = capsys.readouterr()
    assert "Game loaded successfully" in captured.out or "Loaded" in captured.out


def test_cli_exit_branch(monkeypatch, capsys):
    """Test that command 3 exits the CLI loop."""
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        return "3"  # Exit

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)
    
    # cli() uses break, not exit(), so it returns normally
    cli()
    captured = capsys.readouterr()
    assert "Thanks for playing" in captured.out


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

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)
    monkeypatch.setattr("cli.start_new_game", lambda: GameEngine(setup_data("Test")))
    monkeypatch.setattr("cli.load_game", lambda: GameEngine(setup_data("Test")))
    monkeypatch.setattr("cli.game_loop", lambda engine: None)

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

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)
    monkeypatch.setattr("cli.start_new_game", lambda: GameEngine(setup_data("Test")))
    monkeypatch.setattr("cli.load_game", lambda: GameEngine(setup_data("Test")))
    monkeypatch.setattr("cli.game_loop", lambda engine: None)

    cli()
    captured = capsys.readouterr()
    # Should show errors for invalid inputs
    assert "Invalid choice" in captured.out or "Error" in captured.out
    # Should eventually exit
    assert "Thanks for playing" in captured.out


def test_load_game_file_not_found_error(tmp_path, monkeypatch, capsys):
    """Test that FileNotFoundError is handled gracefully when loading."""
    monkeypatch.setattr("persistence.GAME_FILE", tmp_path / "nonexistent.json")
    monkeypatch.setattr("cli.GAME_FILE", tmp_path / "nonexistent.json")

    # Simulate menu command 2 (load)
    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"  # Exit after error

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)
    exit_called = {"called": False}
    monkeypatch.setattr("builtins.exit", lambda: exit_called.update({"called": True}))

    cli()
    captured = capsys.readouterr()
    assert "No save file found" in captured.out or "Error" in captured.out


def test_load_game_json_decode_error(tmp_path, monkeypatch, capsys):
    """Test that JSONDecodeError is handled when file is corrupted."""
    game_file = tmp_path / "game.json"
    game_file.write_text("{invalid json}", encoding="utf-8")
    monkeypatch.setattr("persistence.GAME_FILE", game_file)
    monkeypatch.setattr("cli.GAME_FILE", game_file)

    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)
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
    monkeypatch.setattr("persistence.GAME_FILE", game_file)
    monkeypatch.setattr("cli.GAME_FILE", game_file)

    call_count = {"count": 0}

    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "2"
        else:
            return "3"

    monkeypatch.setattr("cli.Prompt.ask", mock_prompt)
    exit_called = {"called": False}
    monkeypatch.setattr("builtins.exit", lambda: exit_called.update({"called": True}))

    cli()
    captured = capsys.readouterr()
    assert "incompatible" in captured.out or "Error" in captured.out or "Missing key" in captured.out

