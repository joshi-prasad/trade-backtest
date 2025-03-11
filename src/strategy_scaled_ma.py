from typing import List, Dict, Any, Tuple
from datetime import datetime
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
Swing Trading Strategy (Daily Chart) - Long Trades Only
- This strategy follows a two-step approach, starting with a test trade
before committing the full capital.

Strategy Rules
1. Test Trade (Entry with 10% of Capital)
a. Enter a test trade when Price > 5-day MA > 20-day MA.
b. Test Trade Exit Conditions
- Exit the test trade if either of the following occurs:
  - Price drops below the 20-day MA.
  - Price drops below the 150-day MA.

2. Scaling into the Trade
If the test trade gains more than 10%, deploy the remaining 90% of the capital
into the trade.
a. Full Trade Exit Condition
- Exit the entire position if the price drops below the 150-day MA.
"""


class ScaledMaStrategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        """
        Initialize scaled MA strategy with test trades

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.test_trade_amount = initial_investment * 0.10  # 10% for test trade
        self.full_trade_amount = initial_investment * 0.99  # 90% for scaling in
        self.max_loss_pct = 5.0  # Maximum allowed loss for scaled position

        # Initialize moving averages
        self.ma5 = EMA(5)     # 5-day MA for entry
        self.ma20 = EMA(20)   # 20-day MA for entry and test trade exit
        self.ma150 = EMA(150) # 150-day MA for final exit

        # Separate trade lists for analysis
        self.trades: List[Trade] = []
        self.test_trades: List[Trade] = []
        self.scaled_trades: List[Trade] = []

    def run(self) -> Tuple[StrategyStats, Dict[str, StrategyStats]]:
        """
        Run the strategy and return statistics

        Returns:
            Tuple containing:
            - Overall strategy statistics
            - Dictionary with separate statistics for test and scaled trades
        """
        # Read data
        data = self.reader.get_data_as_lists()
        dates = data['dates']
        closes = data['close']

        # Calculate MAs
        ma5_values = []
        ma20_values = []
        ma150_values = []

        for price in closes:
            self.ma5.push(price)
            self.ma20.push(price)
            self.ma150.push(price)
            ma5_values.append(self.ma5.get_ema())
            ma20_values.append(self.ma20.get_ema())
            ma150_values.append(self.ma150.get_ema())

        # Trading state variables
        in_test_trade = False
        in_scaled_trade = False
        test_entry_date = None
        test_entry_price = None
        scaled_entry_date = None
        scaled_entry_price = None

        # Start checking for trades after all MAs have enough data
        start_idx = 150  # Start after longest MA has enough data

        for i in range(start_idx, len(closes)):
            current_price = closes[i]
            current_date = dates[i]

            # Skip if we don't have valid MA values
            if not all([ma5_values[i], ma20_values[i], ma150_values[i]]):
                continue

            # Check exit conditions first
            if in_test_trade or in_scaled_trade:
                test_trade_exit = False
                full_position_exit = False
                exit_reason = ""

                # Check test trade exit conditions
                if in_test_trade and not in_scaled_trade:
                    if (current_price < ma20_values[i] or
                        current_price < ma150_values[i]):
                        test_trade_exit = True
                        exit_reason = "MA-based exit"

                # Check scaled position exit conditions
                if in_scaled_trade:
                    scaled_profit = ((current_price - scaled_entry_price) / scaled_entry_price) * 100

                    # Exit on MA condition or stop loss
                    if current_price < ma150_values[i]:
                        full_position_exit = True
                        exit_reason = "MA-based exit"
                    elif scaled_profit <= -self.max_loss_pct:
                        full_position_exit = True
                        exit_reason = f"Stop loss triggered at {scaled_profit:.2f}%"

                # Handle exits
                if test_trade_exit or full_position_exit:
                    # Exit test trade if active
                    if in_test_trade:
                        test_profit = ((current_price - test_entry_price) / test_entry_price) * 100
                        print(f"\nExiting test trade ({exit_reason}):")
                        print(f"Entry: {test_entry_date.strftime('%Y-%m-%d')} at {test_entry_price:.2f}")
                        print(f"Exit: {current_date.strftime('%Y-%m-%d')} at {current_price:.2f}")
                        print(f"Profit: {test_profit:.2f}%")

                        self.test_trades.append(Trade(
                            entry_date=test_entry_date,
                            entry_price=test_entry_price,
                            exit_date=current_date,
                            exit_price=current_price
                        ))
                        in_test_trade = False

                    # Exit scaled trade if active
                    if in_scaled_trade:
                        scaled_profit = ((current_price - scaled_entry_price) / scaled_entry_price) * 100
                        print(f"\nExiting scaled trade ({exit_reason}):")
                        print(f"Entry: {scaled_entry_date.strftime('%Y-%m-%d')} at {scaled_entry_price:.2f}")
                        print(f"Exit: {current_date.strftime('%Y-%m-%d')} at {current_price:.2f}")
                        print(f"Profit: {scaled_profit:.2f}%")

                        self.scaled_trades.append(Trade(
                            entry_date=scaled_entry_date,
                            entry_price=scaled_entry_price,
                            exit_date=current_date,
                            exit_price=current_price
                        ))
                        in_scaled_trade = False

                    continue

            # Check scaling conditions if in test trade
            if in_test_trade and not in_scaled_trade:
                test_trade_profit = ((current_price - test_entry_price) / test_entry_price) * 100
                if test_trade_profit >= 5:  # Scale in if test trade is up 10%
                    in_scaled_trade = True
                    scaled_entry_date = current_date
                    scaled_entry_price = current_price
                    print(f"\nScaling in (test trade up {test_trade_profit:.2f}%):")
                    print(f"Entry price: {current_price:.2f}")

            # Check entry conditions for new test trade
            if not in_test_trade and not in_scaled_trade:
                # Check if Price > 5MA > 20MA
                if (current_price > ma5_values[i] and
                    ma5_values[i] > ma20_values[i]):

                    in_test_trade = True
                    test_entry_date = current_date
                    test_entry_price = current_price
                    print(f"\nEntering test trade:")
                    print(f"Entry price: {current_price:.2f}")

        # Close any open trades at the end
        if in_test_trade:
            final_test_profit = ((closes[-1] - test_entry_price) / test_entry_price) * 100
            print(f"\nClosing open test trade:")
            print(f"Entry: {test_entry_date.strftime('%Y-%m-%d')} at {test_entry_price:.2f}")
            print(f"Exit: {dates[-1].strftime('%Y-%m-%d')} at {closes[-1]:.2f}")
            print(f"Profit: {final_test_profit:.2f}%")

            self.test_trades.append(Trade(
                entry_date=test_entry_date,
                entry_price=test_entry_price,
                exit_date=dates[-1],
                exit_price=closes[-1]
            ))

        if in_scaled_trade:
            final_scaled_profit = ((closes[-1] - scaled_entry_price) / scaled_entry_price) * 100
            print(f"\nClosing open scaled trade:")
            print(f"Entry: {scaled_entry_date.strftime('%Y-%m-%d')} at {scaled_entry_price:.2f}")
            print(f"Exit: {dates[-1].strftime('%Y-%m-%d')} at {closes[-1]:.2f}")
            print(f"Profit: {final_scaled_profit:.2f}%")

            self.scaled_trades.append(Trade(
                entry_date=scaled_entry_date,
                entry_price=scaled_entry_price,
                exit_date=dates[-1],
                exit_price=closes[-1]
            ))

        # Combine all trades for overall statistics
        self.trades = self.test_trades + self.scaled_trades

        # Calculate statistics
        overall_stats = StrategyStats(self.trades, self.initial_investment)
        test_stats = StrategyStats(self.test_trades, self.test_trade_amount)
        scaled_stats = StrategyStats(self.scaled_trades, self.full_trade_amount)

        detailed_stats = {
            'test_trades': test_stats,
            'scaled_trades': scaled_stats
        }

        return overall_stats, detailed_stats

def main():
    """Example usage of the scaled MA strategy"""
    strategy = ScaledMaStrategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000
    )
    overall_stats, detailed_stats = strategy.run()

    # print("\nOverall Strategy Performance:")
    # print("===========================")
    # print(overall_stats)

    print("\nTest Trades Performance (10% Capital):")
    print("===================================")
    print(detailed_stats['test_trades'])

    print("\nScaled Trades Performance (90% Capital):")
    print("=====================================")
    print(detailed_stats['scaled_trades'])

if __name__ == "__main__":
    main()