from typing import List, Dict, Any
from datetime import datetime
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
A swing trading strategy based on EMA crossovers and trend following. The
strategy uses a 10-period EMA for short-term momentum and a 200-period EMA for
long-term trend identification. It enters long positions when the 10 EMA
crosses above the 200 EMA in an uptrend, and exits when the index closes below
the 200 EMA. This helps capture intermediate price swings while
maintaining alignment with the broader market trend.
"""

class SwingStrategy:
    def __init__(self, file_path: str):
        """
        Initialize swing trading strategy

        Args:
            file_path (str): Path to the CSV file containing index data
        """
        self.reader = IndexCSVReader(file_path)
        self.data = None
        self.trades: List[Trade] = []

        # Initialize EMAs
        self.ema10 = EMA(10)
        self.ema200 = EMA(200)

    def run(self) -> StrategyStats:
        """
        Run the strategy and return statistics

        Returns:
            StrategyStats: Computed strategy statistics
        """
        # Read data
        self.data = self.reader.get_data_as_lists()
        dates = self.data['dates']
        closes = self.data['close']

        # Calculate EMAs
        ema10_values = []
        ema200_values = []

        for price in closes:
            self.ema10.push(price)
            self.ema200.push(price)
            ema10_values.append(self.ema10.get_ema())
            ema200_values.append(self.ema200.get_ema())

        # Look for trading opportunities
        in_trade = False
        entry_date = None
        entry_price = None

        # Start checking for trades after both EMAs have enough data
        start_idx = 200  # Start after EMA200 has enough data

        for i in range(start_idx, len(closes)):
            current_price = closes[i]
            current_date = dates[i]

            # Skip if we don't have valid EMA values
            if not ema10_values[i] or not ema200_values[i]:
                assert False, f"EMA values are not valid for date: {current_date}"
                continue

            if not in_trade:
                # Check entry conditions
                if (current_price > ema10_values[i] and
                    current_price > ema200_values[i] and
                    ema10_values[i] > ema200_values[i]):

                    in_trade = True
                    entry_date = current_date
                    entry_price = current_price

            else:
                # Check exit conditions
                if current_price < ema200_values[i]:
                    # Exit the trade
                    # print(f"Entry date: {entry_date}, "
                    #     f"Entry price: {entry_price}, "
                    #     f"Exit date: {current_date}, "
                    #     f"Exit price: {current_price}")
                    self.trades.append(Trade(
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_trade = False

        # Close any open trade at the end of the period
        if in_trade:
            # print(f"Entry date: {entry_date}, "
            #     f"Entry price: {entry_price}, "
            #     f"Exit date: {dates[-1]}, "
            #     f"Exit price: {closes[-1]}")
            self.trades.append(Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=dates[-1],
                exit_price=closes[-1]
            ))

        # Calculate and return statistics
        return StrategyStats(self.trades, initial_investment=1000000)

def main():
    """Example usage of the swing trading strategy"""
    # Initialize and run strategy
    strategy = SwingStrategy("../indices_data/nifty_midcap_50.csv")
    stats = strategy.run()

    # Print statistics
    print(stats)

if __name__ == "__main__":
    main()