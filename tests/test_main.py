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
    monkeypatch.setattr("main.Prompt.ask", lambda _: "Bob")
    engine = start_new_game()
    assert isinstance(engine, GameEngine)
    assert engine.player.name == "Bob"


def test_store_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("main.GAME_FILE", tmp_path / "game.json")
    engine = start_new_game(player_name="Carol")

    store_game(engine)
    loaded_engine = load_game()

    assert isinstance(loaded_engine, GameEngine)
    assert loaded_engine.player.name == engine.player.name
    assert loaded_engine.game.current_day == engine.game.current_day
    assert loaded_engine.game.cities[0].name == engine.game.cities[0].name


def test_serialize_and_deserialize_are_inverse(tmp_path, monkeypatch):
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
    monkeypatch.setattr("main.GAME_FILE", tmp_path / "game.json")
    monkeypatch.setattr("main.Prompt.ask", lambda *args, **kwargs: "1")
    monkeypatch.setattr("main.start_new_game", lambda: start_new_game(player_name="Eve"))

    cli()
    captured = capsys.readouterr()
    assert "Starting a new game" in captured.out
    assert tmp_path.joinpath("game.json").exists()


def test_cli_handles_invalid_command(monkeypatch, capsys):
    monkeypatch.setattr("main.Prompt.ask", lambda *args, **kwargs: "invalid")

    cli()
    captured = capsys.readouterr()
    assert "Invalid command" in captured.out


def test_cli_load_branch(monkeypatch, capsys):
    monkeypatch.setattr("main.Prompt.ask", lambda *args, **kwargs: "2")
    monkeypatch.setattr("main.load_game", lambda: start_new_game(player_name="Loaded"))

    cli()
    captured = capsys.readouterr()
    assert "Game loaded" in captured.out
    assert "Loaded" in captured.out


def test_cli_exit_branch(monkeypatch, capsys):
    monkeypatch.setattr("main.Prompt.ask", lambda *args, **kwargs: "3")
    exit_called = {}
    monkeypatch.setattr("builtins.exit", lambda: exit_called.setdefault("called", True))

    cli()
    assert exit_called.get("called") is True


def test_render_main_menu_outputs_menu():
    buffer = StringIO()
    console = Console(file=buffer, width=60, force_terminal=True, color_system=None)

    _render_main_menu(console)

    output = buffer.getvalue()
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
    