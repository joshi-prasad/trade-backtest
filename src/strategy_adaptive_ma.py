from typing import List, Dict, Any
from datetime import datetime
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
An AdaptiveMaStrategy class that implements the strategy with adaptive exit
conditions. Here are the key features:

1. Moving Averages Used:
a. 10-day MA for entry signal
b. 20-day MA for entry confirmation and initial exit
c. 100-day MA for trailing exit after 10% profit

2. Entry Conditions:
a. Price > 10-day MA
b. 10-day MA > 20-day MA

3. Adaptive Exit Conditions:
a. Before 10% profit: Exit when price < 20-day MA
b. After 10% profit: Exit when price < 100-day MA
"""

class AdaptiveMaStrategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        """
        Initialize adaptive MA strategy with different exit conditions based on profit

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment

        # Initialize moving averages
        self.ma10 = EMA(10)  # 10-day MA for entry
        self.ma20 = EMA(20)  # 20-day MA for entry and initial exit
        self.ma100 = EMA(100)  # 100-day MA for trailing exit

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

        # Calculate MAs
        ma10_values = []
        ma20_values = []
        ma100_values = []

        for price in closes:
            self.ma10.push(price)
            self.ma20.push(price)
            self.ma100.push(price)
            ma10_values.append(self.ma10.get_ema())
            ma20_values.append(self.ma20.get_ema())
            ma100_values.append(self.ma100.get_ema())

        # Trading state variables
        in_trade = False
        entry_date = None
        entry_price = None
        achieved_10_percent = False

        # Start checking for trades after all MAs have enough data
        start_idx = 100  # Start after longest MA has enough data

        for i in range(start_idx, len(closes)):
            current_price = closes[i]
            current_date = dates[i]

            # Skip if we don't have valid MA values
            if not all([ma10_values[i], ma20_values[i], ma100_values[i]]):
                continue

            if in_trade:
                # Calculate current profit percentage
                current_profit = ((current_price - entry_price) / entry_price) * 100

                # Update flag if we've achieved 10% profit
                if not achieved_10_percent and current_profit >= 10:
                    achieved_10_percent = True
                    print(f"Trade achieved 10% profit on {current_date.strftime('%Y-%m-%d')} "
                          f"at price {current_price:.2f}")

                # Check exit conditions based on profit level
                exit_triggered = False

                if achieved_10_percent:
                    # Exit only if price closes below 100-day MA
                    if current_price < ma100_values[i]:
                        exit_triggered = True
                        exit_reason = "Price below 100MA after 10% profit"
                else:
                    # Exit if price closes below 20-day MA
                    if current_price < ma20_values[i]:
                        exit_triggered = True
                        exit_reason = "Price below 20MA before 10% profit"

                if exit_triggered:
                    print(f"Exit trade - {exit_reason}")
                    print(f"Entry: {entry_date.strftime('%Y-%m-%d')} at {entry_price:.2f}")
                    print(f"Exit: {current_date.strftime('%Y-%m-%d')} at {current_price:.2f}")
                    print(f"Profit: {current_profit:.2f}%")
                    print("---")

                    self.trades.append(Trade(
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))

                    # Reset trade variables
                    in_trade = False
                    achieved_10_percent = False

            else:
                # Check entry conditions
                if (current_price > ma10_values[i] and
                    ma10_values[i] > ma20_values[i]):

                    in_trade = True
                    entry_date = current_date
                    entry_price = current_price
                    achieved_10_percent = False

                    print(f"\nEnter trade on {entry_date.strftime('%Y-%m-%d')} "
                          f"at price {entry_price:.2f}")

        # Close any open trade at the end of the period
        if in_trade:
            final_profit = ((closes[-1] - entry_price) / entry_price) * 100
            print(f"\nClosing open trade at end of period:")
            print(f"Entry: {entry_date.strftime('%Y-%m-%d')} at {entry_price:.2f}")
            print(f"Exit: {dates[-1].strftime('%Y-%m-%d')} at {closes[-1]:.2f}")
            print(f"Profit: {final_profit:.2f}%")

            self.trades.append(Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=dates[-1],
                exit_price=closes[-1]
            ))

        # Calculate and return statistics
        return StrategyStats(self.trades, self.initial_investment)

def main():
    """Example usage of the adaptive MA strategy"""
    # Initialize and run strategy
    strategy = AdaptiveMaStrategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000
    )
    stats = strategy.run()

    # Print statistics
    print("\nAdaptive MA Strategy Results:")
    print("===========================")
    print(stats)

if __name__ == "__main__":
    main()