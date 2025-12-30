"""
CLI entrypoint for Fruit Dealer Game.

This module serves as the main entry point, delegating to cli.py.
All money values are stored as cents (int) to avoid floating point issues.
"""

from cli import cli


if __name__ == "__main__":
    cli()
