"""
Pricing System for Fruit Dealer Game

This module handles dynamic price calculation for fruits across all city markets.
Prices are influenced by:
    1. Base price of the fruit (defined in Fruit model)
    2. City specialty modifiers (cities can have cheaper/expensive fruits)
    3. Daily random variance (±20% to simulate market fluctuations)

Usage:
    pricing = PricingSystem(game)
    pricing.regenerate_all_prices()  # Call this when day changes
    price = pricing.get_price(apple, tokyo)
"""

from models import City, Fruit, Money, Game, Market
from typing import Dict, List
import random


class PricingSystem:
    """
    Manages price calculation and storage for all markets in the game.
    
    The PricingSystem doesn't store prices itself - it calculates them
    and writes directly to each Market object in game.markets.
    This keeps Market as the single source of truth for current prices.
    """
    
    def __init__(self, game: Game):
        """
        Initialize the pricing system with a reference to the game state.
        
        Args:
            game: The Game object containing fruits, cities, and markets
        """
        self.game = game
        # Generate initial prices for all markets on game start
        self.regenerate_all_prices()

    def regenerate_all_prices(self) -> None:
        """
        Regenerate prices for ALL markets in the game.
        
        Call this method when:
            - The game starts (handled automatically in __init__)
            - A new day begins (triggered by GameEngine.advance_day())
        
        Each fruit in each city gets unique randomness applied.
        """
        for market in self.game.markets:
            # Calculate new prices for this market's city
            new_prices = self._calculate_market_prices(
                city=market.city,
                fruits=self.game.fruits
            )
            # Update the market's prices directly
            market.prices = new_prices

    def _calculate_market_prices(self, city: City, fruits: List[Fruit]) -> Dict[str, Money]:
        """
        Calculate prices for all fruits in a single city.
        
        This is a PRIVATE helper method (note the underscore prefix).
        External code should call regenerate_all_prices() instead.
        
        Price formula: base_price * city_modifier * random_factor
        
        Args:
            city: The city to calculate prices for
            fruits: List of all fruits in the game
            
        Returns:
            Dict mapping fruit name to calculated price in cents
        """
        prices: Dict[str, Money] = {}
        
        for fruit in fruits:
            # Get city's specialty modifier for this fruit
            # Default to 1.0 (neutral) if city doesn't specialize in this fruit
            # Values < 1.0 mean cheaper (city produces it)
            # Values > 1.0 mean more expensive (city imports it)
            city_modifier = city.specialties.get(fruit.name, 1.0)
            
            # Each fruit gets its own random variance (±20%)
            # This creates daily market fluctuations
            random_factor = random.uniform(0.8, 1.2)
            
            # Calculate final price
            price = fruit.base_price * city_modifier * random_factor
            
            # Convert to int (Money is in cents, no fractional cents)
            prices[fruit.name] = int(price)
        
        return prices

    def get_price(self, fruit_name: str, city_name: str) -> Money:
        """
        Look up the current price for a fruit in a specific city.
        
        Args:
            fruit_name: Name of the fruit (e.g., "Apple")
            city_name: Name of the city (e.g., "Tokyo")
            
        Returns:
            Current price in cents, or 0 if fruit/city not found
            
        Note:
            This retrieves pre-calculated prices from Market objects.
            Prices are only recalculated when regenerate_all_prices() is called.
        """
        # Find the market for this city
        for market in self.game.markets:
            if market.city.name == city_name:
                # Return the fruit's price if it exists in this market
                return market.prices.get(fruit_name, 0)
        
        # City not found - this shouldn't happen in normal gameplay
        return 0
