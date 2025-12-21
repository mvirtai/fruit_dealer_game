"""
Systems package for Fruit Dealer Game.

Contains game logic systems that operate on the data models.
Systems are stateless processors that manipulate game state.

Available systems:
    - PricingSystem: Handles dynamic fruit price calculation
"""

from systems.pricing import PricingSystem

__all__ = ["PricingSystem"]

