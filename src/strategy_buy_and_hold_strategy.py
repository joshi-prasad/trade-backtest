from typing import List
from datetime import datetime
from index_csv_reader import IndexCSVReader
from strategy_stats import Trade, StrategyStats

class BuyAndHoldStrategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        """
        Initialize buy and hold strategy

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.trades: List[Trade] = []

    def run(self) -> StrategyStats:
        """
        Run the strategy and return statistics

        Returns:
            StrategyStats: Computed strategy statistics
        """
        # Read data
        data = self.reader.get_data_as_lists()
        dates = data['dates']
        closes = data['close']

        # Get first and last dates and prices
        entry_date = dates[0]
        entry_price = closes[0]
        exit_date = dates[-1]
        exit_price = closes[-1]

        # Create single trade for entire period
        trade = Trade(
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=exit_date,
            exit_price=exit_price
        )

        self.trades.append(trade)

        # Print trade details
        print(f"\nBuy and Hold Trade Details:")
        print(f"==========================")
        print(f"Entry Date: {entry_date.strftime('%Y-%m-%d')}")
        print(f"Entry Price: ₹{entry_price:,.2f}")
        print(f"Exit Date: {exit_date.strftime('%Y-%m-%d')}")
        print(f"Exit Price: ₹{exit_price:,.2f}")
        print(f"Holding Period: {trade.holding_period} days")
        print(f"Total Return: {trade.profit_pct:.2f}%")

        # Calculate and return statistics
        return StrategyStats(self.trades, self.initial_investment)

def main():
    """Example usage of the buy and hold strategy"""
    # Initialize and run strategy
    strategy = BuyAndHoldStrategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000
    )
    stats = strategy.run()

    # Print statistics
    print("\nBuy and Hold Strategy Results:")
    print("============================")
    print(stats)

if __name__ == "__main__":
    main()