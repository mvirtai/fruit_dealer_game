from models import Game, Market, Player
from systems.pricing import PricingSystem


class GameEngine:
    def __init__(self, game: Game):
        self.game = game
        self.pricing = PricingSystem(game)

    @property
    def player(self) -> Player:
        """Single-player helper - first player in list."""
        return self.game.player

    def buy(self, fruit_name: str, quantity: int) -> bool:
        market = self._get_current_market()
        if fruit_name not in market.prices:
            raise ValueError(f"Fruit not found in market: {fruit_name}")

        price = market.prices[fruit_name]
        total_cost = price * quantity

        if total_cost > self.player.money:
            raise ValueError(f"Not enough money to buy {quantity} {fruit_name}")

        self.player.money -= total_cost
        current = self.player.inventory.get(fruit_name, 0)
        self.player.inventory[fruit_name] = current + quantity
        return True

    def sell(self, fruit_name: str, quantity: int) -> bool:
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
        city = next((c for c in self.game.cities if c.name == city_name), None)
        if not city:
            raise ValueError(f"City not found: {city_name}")

        self.player.city = city
        self.advance_day()
        return True

    def advance_day(self) -> None:
        self.game.day += 1
        self.pricing.regenerate_all_prices()

    def _get_current_market(self) -> Market:
        """Helper to get the market for player's current city."""
        market = next(
            (m for m in self.game.markets
             if m.city.name == self.player.city.name),
            None
        )
        if not market:
            raise ValueError(f"No market for: {self.player.city.name}")
        return market