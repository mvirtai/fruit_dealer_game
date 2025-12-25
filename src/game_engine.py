"""
Game Engine for Fruit Dealer Game

This module contains the GameEngine class, which serves as the central controller
for all game logic. It handles player actions such as buying, selling, and traveling,
while managing game state and coordinating with other systems like PricingSystem.

Usage:
    engine = GameEngine(game)
    engine.buy("Apple", 5)
    engine.sell("Banana", 2)
    engine.travel("Tokyo")
"""

from models import Game, Market, Player
from systems.pricing import PricingSystem


class GameEngine:
    """
    Central game controller that manages player actions and game state.
    
    The GameEngine coordinates between game models (Player, Market, Game) and
    systems (PricingSystem) to execute player commands and maintain game rules.
    All player actions go through this class to ensure consistency.
    """
    
    def __init__(self, game: Game):
        """
        Initialize the game engine with a game state.
        
        Args:
            game: The Game object containing all game state (player, cities, markets, fruits)
        """
        self.game = game
        self.pricing = PricingSystem(game)


    @property
    def player(self) -> Player:
        """
        Get the current player object.
        
        Returns:
            The Player object from the game state
        """
        return self.game.player


    def buy(self, fruit_name: str, quantity: int) -> bool:
        """
        Buy fruits from the current city's market.
        
        Args:
            fruit_name: Name of the fruit to buy (e.g., "Apple")
            quantity: Number of fruits to buy
            
        Returns:
            True if purchase was successful
            
        Raises:
            ValueError: If fruit is not available in current market
            ValueError: If player doesn't have enough money
        """
        market = self._get_current_market()
        if fruit_name not in market.prices:
            raise ValueError(f"Fruit not found in market: {fruit_name}")

        price = market.prices[fruit_name]
        total_cost = price * quantity

        if total_cost > self.player.money:
            raise ValueError(f"Not enough funds to buy {quantity} {fruit_name}")

        self.player.money -= total_cost
        current = self.player.inventory.get(fruit_name, 0)
        self.player.inventory[fruit_name] = current + quantity
        return True


    def sell(self, fruit_name: str, quantity: int) -> bool:
        """
        Sell fruits to the current city's market.
        
        Args:
            fruit_name: Name of the fruit to sell (e.g., "Apple")
            quantity: Number of fruits to sell
            
        Returns:
            True if sale was successful
            
        Raises:
            ValueError: If fruit is not available in current market
            ValueError: If player doesn't have enough inventory
        """
        market = self._get_current_market()
        if fruit_name not in market.prices:
            raise ValueError(f"Fruit not found in market: {fruit_name}")

        current_qty = self.player.inventory.get(fruit_name, 0)
        if quantity > current_qty:
            raise ValueError(f"Not enough {fruit_name} to sell {quantity}")

        price = market.prices[fruit_name]
        self.player.money += price * quantity
        self.player.inventory[fruit_name] = current_qty - quantity
        return True


    def travel(self, city_name: str) -> bool:
        """
        Travel to a different city.
        
        Traveling costs money and advances the game by one day, which triggers
        price regeneration in all markets.
        
        Args:
            city_name: Name of the destination city (e.g., "Tokyo")
            
        Returns:
            True if travel was successful
            
        Raises:
            ValueError: If city doesn't exist in the game
            ValueError: If player doesn't have enough money for travel cost
        """
        city = next((c for c in self.game.cities if c.name == city_name), None)
        if not city:
            raise ValueError(f"City not found: {city_name}")

        travel_cost = 50

        if self.player.money < travel_cost:
            raise ValueError(
                f"Not enough funds to travel to {city_name}. "
                f"You need {travel_cost} more."
            )
        
        self.player.money -= travel_cost
        self.player.current_city = city 
        self._advance_day()
        return True

    def _advance_day(self) -> bool:
        """
        Advance the game by one day and regenerate all market prices.
        
        This is a PRIVATE helper method (note the underscore prefix).
        External code should call travel() instead, which handles day advancement.
        
        Returns:
            True when day advancement is complete
        """
        self.game.current_day += 1
        self.pricing.regenerate_all_prices()
        return True
    
    def _get_current_market(self) -> Market:
        """
        Get the market object for the player's current city.
        
        This is a PRIVATE helper method (note the underscore prefix).
        Used internally by buy() and sell() to access current market prices.
        
        Returns:
            Market object for the current city
            
        Raises:
            ValueError: If no market exists for the current city
        """
        market = next(
            (m for m in self.game.markets
             if m.city.name == self.player.current_city.name),
            None
        )
        if not market:
            raise ValueError(f"No market for {self.player.current_city.name}")
        return market