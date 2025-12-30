"""
Tests for commands module.

Tests command parsing, execution, and game loop functionality.
"""

import pytest
from pathlib import Path

from commands import pluralize, parse_command, execute_command, game_loop, COMMANDS
from game_engine import GameEngine
from models import Game, Fruit, City, Player, Market
from conftest import make_game, apple, banana, pori, helsinki


# --- Test pluralize ---

def test_pluralize_singular():
    """Test that singular count returns singular form."""
    assert pluralize("apple", 1) == "apple"
    assert pluralize("orange", 1) == "orange"
    assert pluralize("banana", 1) == "banana"


def test_pluralize_plural():
    """Test that plural count returns plural form."""
    assert pluralize("apple", 2) == "apples"
    assert pluralize("orange", 0) == "oranges"
    assert pluralize("banana", 10) == "bananas"


def test_pluralize_edge_cases():
    """Test edge cases for pluralize."""
    assert pluralize("", 1) == ""
    assert pluralize("", 2) == "s"
    assert pluralize("test", -1) == "tests"  # Negative counts still pluralize


# --- Test parse_command ---

def test_parse_command_valid_commands(monkeypatch):
    """Test parsing valid commands."""
    calls = []
    def mock_render_error(msg, hint=None):
        calls.append((msg, hint))
    
    monkeypatch.setattr("commands.render_error", mock_render_error)
    
    # Commands without args
    assert parse_command("help") == ("help", [])
    assert parse_command("status") == ("status", [])
    assert parse_command("save") == ("save", [])
    assert parse_command("quit") == ("quit", [])
    assert parse_command("exit") == ("exit", [])
    
    # Commands with single arg
    assert parse_command("travel Tampere") == ("travel", ["Tampere"])
    assert parse_command("travel  Helsinki") == ("travel", ["Helsinki"])  # Extra space
    
    # Commands with multiple args
    assert parse_command("buy apple 5") == ("buy", ["apple", "5"])
    assert parse_command("sell banana 10") == ("sell", ["banana", "10"])
    
    # Case insensitivity
    assert parse_command("HELP") == ("help", [])
    assert parse_command("Buy Apple 5") == ("buy", ["Apple", "5"])
    
    # No error calls for valid commands
    assert len(calls) == 0


def test_parse_command_edge_cases(monkeypatch):
    """Test edge cases for parse_command."""
    calls = []
    def mock_render_error(msg, hint=None):
        calls.append((msg, hint))
    
    monkeypatch.setattr("commands.render_error", mock_render_error)
    
    # Empty strings
    assert parse_command("") is None
    assert parse_command("   ") is None  # Only whitespace
    
    # Invalid commands
    assert parse_command("invalid") is None
    assert len(calls) == 1
    assert "Invalid command" in calls[0][0]
    
    calls.clear()
    assert parse_command("lease apple 5") is None
    assert len(calls) == 1


def test_parse_command_whitespace_handling(monkeypatch):
    """Test that whitespace is handled correctly."""
    monkeypatch.setattr("commands.render_error", lambda *args, **kwargs: None)
    
    assert parse_command("  help  ") == ("help", [])
    assert parse_command("buy  apple  5") == ("buy", ["apple", "5"])


# --- Test execute_command ---

@pytest.fixture
def mock_ui(monkeypatch):
    """Fixture to mock UI rendering functions."""
    error_calls = []
    success_calls = []
    
    def mock_render_error(msg, hint=None):
        error_calls.append((msg, hint))
    
    def mock_render_success(msg):
        success_calls.append((msg,))
    
    def mock_render_game_view(engine):
        pass  # No-op for tests
    
    monkeypatch.setattr("commands.render_error", mock_render_error)
    monkeypatch.setattr("commands.render_success", mock_render_success)
    monkeypatch.setattr("commands.render_game_view", mock_render_game_view)
    
    return {"error": error_calls, "success": success_calls}


def test_execute_command_help(mock_ui, make_game, apple, pori):
    """Test help command."""
    engine = GameEngine(make_game(fruits=[apple], cities=[pori]))
    result = execute_command(engine, "help", [])
    assert result is True


def test_execute_command_status(mock_ui, make_game, apple, pori):
    """Test status command."""
    engine = GameEngine(make_game(fruits=[apple], cities=[pori]))
    result = execute_command(engine, "status", [])
    assert result is True


def test_execute_command_save(mock_ui, tmp_path, monkeypatch, make_game, apple, pori):
    """Test save command."""
    save_path = tmp_path / "test_save.json"
    monkeypatch.setattr("persistence.GAME_FILE", save_path)
    monkeypatch.setattr("commands.store_game", lambda engine, path=None: None)
    
    engine = GameEngine(make_game(fruits=[apple], cities=[pori]))
    result = execute_command(engine, "save", [])
    assert result is True
    assert len(mock_ui["success"]) == 1
    assert "saved" in mock_ui["success"][0][0].lower()


def test_execute_command_quit_exit(mock_ui, make_game, apple, pori):
    """Test quit and exit commands."""
    engine = GameEngine(make_game(fruits=[apple], cities=[pori]))
    
    result = execute_command(engine, "quit", [])
    assert result is False
    
    result = execute_command(engine, "exit", [])
    assert result is False


def test_execute_command_buy_success(mock_ui, monkeypatch, make_game, apple, pori):
    """Test successful buy command."""
    game = make_game(fruits=[apple], cities=[pori], player_money=10000)
    engine = GameEngine(game)
    
    # Mock pricing to return known price
    original_get_price = engine.pricing.get_price
    engine.pricing.get_price = lambda fruit, city: 100
    
    result = execute_command(engine, "buy", ["apple", "5"])
    assert result is True
    assert len(mock_ui["success"]) == 1
    assert "Bought" in mock_ui["success"][0][0]
    assert engine.player.inventory.get("Apple", 0) == 5


def test_execute_command_buy_invalid_args(mock_ui, make_game, apple, pori):
    """Test buy command with invalid arguments."""
    engine = GameEngine(make_game(fruits=[apple], cities=[pori]))
    
    # Missing args
    result = execute_command(engine, "buy", ["apple"])
    assert result is True
    assert len(mock_ui["error"]) >= 1
    assert "Usage" in mock_ui["error"][0][0]
    
    mock_ui["error"].clear()
    
    # Invalid quantity
    result = execute_command(engine, "buy", ["apple", "abc"])
    assert result is True
    assert len(mock_ui["error"]) >= 1
    assert "number" in mock_ui["error"][0][0].lower()


def test_execute_command_buy_game_error(mock_ui, monkeypatch, make_game, apple, pori):
    """Test buy command when game engine raises error."""
    game = make_game(fruits=[apple], cities=[pori], player_money=10)
    engine = GameEngine(game)
    
    # Price is higher than available money
    result = execute_command(engine, "buy", ["apple", "1"])
    assert result is True
    # Should have error from game engine
    assert len(mock_ui["error"]) >= 1


def test_execute_command_sell_success(mock_ui, make_game, apple, pori):
    """Test successful sell command."""
    game = make_game(
        fruits=[apple], 
        cities=[pori], 
        player_money=1000,
        player_inventory={"Apple": 5}
    )
    engine = GameEngine(game)
    
    initial_money = engine.player.money
    initial_inventory = engine.player.inventory["Apple"]
    
    result = execute_command(engine, "sell", ["apple", "2"])
    assert result is True
    assert len(mock_ui["success"]) == 1
    assert "Sold" in mock_ui["success"][0][0]
    assert engine.player.inventory["Apple"] == initial_inventory - 2
    assert engine.player.money > initial_money


def test_execute_command_sell_invalid_args(mock_ui, make_game, apple, pori):
    """Test sell command with invalid arguments."""
    game = make_game(fruits=[apple], cities=[pori], player_inventory={"Apple": 1})
    engine = GameEngine(game)
    
    # Missing args
    result = execute_command(engine, "sell", ["apple"])
    assert result is True
    assert len(mock_ui["error"]) >= 1
    assert "Usage" in mock_ui["error"][0][0]
    
    mock_ui["error"].clear()
    
    # Invalid quantity
    result = execute_command(engine, "sell", ["apple", "xyz"])
    assert result is True
    assert len(mock_ui["error"]) >= 1
    assert "number" in mock_ui["error"][0][0].lower()


def test_execute_command_sell_game_error(mock_ui, make_game, apple, pori):
    """Test sell command when game engine raises error."""
    game = make_game(fruits=[apple], cities=[pori], player_inventory={"Apple": 1})
    engine = GameEngine(game)
    
    # Try to sell more than available
    result = execute_command(engine, "sell", ["apple", "10"])
    assert result is True
    assert len(mock_ui["error"]) >= 1


def test_execute_command_travel_success(mock_ui, make_game, apple, pori, helsinki):
    """Test successful travel command."""
    game = make_game(
        fruits=[apple], 
        cities=[pori, helsinki], 
        player_money=1000,
        player_city=pori
    )
    engine = GameEngine(game)
    
    initial_city = engine.player.current_city.name
    result = execute_command(engine, "travel", ["helsinki"])
    assert result is True
    assert len(mock_ui["success"]) == 1
    assert "Traveled" in mock_ui["success"][0][0]
    assert engine.player.current_city.name == "Helsinki"
    assert engine.player.current_city.name != initial_city


def test_execute_command_travel_invalid_args(mock_ui, make_game, apple, pori, helsinki):
    """Test travel command with invalid arguments."""
    game = make_game(fruits=[apple], cities=[pori, helsinki])
    engine = GameEngine(game)
    
    # Missing args
    result = execute_command(engine, "travel", [])
    assert result is True
    assert len(mock_ui["error"]) >= 1
    assert "Usage" in mock_ui["error"][0][0]
    
    mock_ui["error"].clear()
    
    # Too many args
    result = execute_command(engine, "travel", ["helsinki", "extra"])
    assert result is True
    assert len(mock_ui["error"]) >= 1


def test_execute_command_travel_game_error(mock_ui, make_game, apple, pori, helsinki):
    """Test travel command when game engine raises error."""
    game = make_game(
        fruits=[apple], 
        cities=[pori, helsinki], 
        player_money=0,  # No money for travel
        player_city=pori
    )
    engine = GameEngine(game)
    
    result = execute_command(engine, "travel", ["InvalidCity"])
    assert result is True
    assert len(mock_ui["error"]) >= 1


def test_execute_command_unknown_command(mock_ui, make_game, apple, pori):
    """Test that unknown commands continue the loop."""
    engine = GameEngine(make_game(fruits=[apple], cities=[pori]))
    
    # This shouldn't happen in practice (parse_command filters), but test anyway
    result = execute_command(engine, "unknown", [])
    assert result is True


def test_execute_command_pluralization(mock_ui, make_game, apple, pori):
    """Test that pluralization works correctly in buy/sell messages."""
    game = make_game(
        fruits=[apple], 
        cities=[pori], 
        player_money=10000,
        player_inventory={"Apple": 5}
    )
    engine = GameEngine(game)
    
    # Buy singular
    engine.pricing.get_price = lambda fruit, city: 100
    result = execute_command(engine, "buy", ["apple", "1"])
    assert "apple" in mock_ui["success"][0][0].lower()
    assert "apples" not in mock_ui["success"][0][0].lower()
    
    mock_ui["success"].clear()
    
    # Buy plural
    result = execute_command(engine, "buy", ["apple", "2"])
    assert "apples" in mock_ui["success"][0][0].lower()
    
    mock_ui["success"].clear()
    
    # Sell singular
    result = execute_command(engine, "sell", ["apple", "1"])
    assert "apple" in mock_ui["success"][0][0].lower()
    assert "apples" not in mock_ui["success"][0][0].lower()
    
    mock_ui["success"].clear()
    
    # Sell plural
    result = execute_command(engine, "sell", ["apple", "2"])
    assert "apples" in mock_ui["success"][0][0].lower()


# --- Test game_loop ---

def test_game_loop_exits_on_quit(monkeypatch, make_game, apple, pori):
    """Test that game loop exits when quit command is entered."""
    game = make_game(fruits=[apple], cities=[pori])
    engine = GameEngine(game)
    
    call_count = {"count": 0}
    
    def mock_render_game_view(engine):
        pass
    
    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "quit"
        return "quit"  # Shouldn't reach here
    
    monkeypatch.setattr("commands.render_game_view", mock_render_game_view)
    monkeypatch.setattr("commands.Prompt.ask", mock_prompt)
    
    # Should return normally (not loop forever)
    game_loop(engine)
    assert call_count["count"] == 1


def test_game_loop_exits_on_exit(monkeypatch, make_game, apple, pori):
    """Test that game loop exits when exit command is entered."""
    game = make_game(fruits=[apple], cities=[pori])
    engine = GameEngine(game)
    
    call_count = {"count": 0}
    
    def mock_render_game_view(engine):
        pass
    
    def mock_prompt(prompt):
        call_count["count"] += 1
        return "exit"
    
    monkeypatch.setattr("commands.render_game_view", mock_render_game_view)
    monkeypatch.setattr("commands.Prompt.ask", mock_prompt)
    
    game_loop(engine)
    assert call_count["count"] == 1


def test_game_loop_continues_on_invalid_command(monkeypatch, make_game, apple, pori):
    """Test that game loop continues when invalid command is entered."""
    game = make_game(fruits=[apple], cities=[pori])
    engine = GameEngine(game)
    
    call_count = {"count": 0}
    
    def mock_render_game_view(engine):
        pass
    
    def mock_prompt(prompt):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return "invalid_command"
        elif call_count["count"] == 2:
            return "status"
        else:
            return "quit"
    
    monkeypatch.setattr("commands.render_game_view", mock_render_game_view)
    monkeypatch.setattr("commands.Prompt.ask", mock_prompt)
    
    game_loop(engine)
    assert call_count["count"] == 3  # invalid, status, quit


def test_game_loop_processes_valid_commands(monkeypatch, make_game, apple, pori):
    """Test that game loop processes multiple valid commands."""
    game = make_game(fruits=[apple], cities=[pori])
    engine = GameEngine(game)
    
    commands = ["status", "save", "help", "quit"]
    call_count = {"count": 0}
    
    def mock_render_game_view(engine):
        pass
    
    def mock_prompt(prompt):
        idx = call_count["count"]
        call_count["count"] += 1
        if idx < len(commands):
            return commands[idx]
        return "quit"
    
    monkeypatch.setattr("commands.render_game_view", mock_render_game_view)
    monkeypatch.setattr("commands.Prompt.ask", mock_prompt)
    monkeypatch.setattr("commands.store_game", lambda engine, path=None: None)
    monkeypatch.setattr("commands.render_success", lambda msg: None)
    
    game_loop(engine)
    assert call_count["count"] == len(commands)
