from typing import List, Dict, Any, Tuple
from datetime import datetime
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
Swing trading strategy based on weekly charts, focusing exclusively on long
trades.

Strategy Rules
1. Initial Test Trade: Enter a long position using 10% of the total available
investment.
2. Entry condition for Initial Test Trade: daily close ≥ 10-day EMA ≥ 200-day
EMA.
3. Scaling In: Invest the remaining 90% only if the initial test trade achieves
at least 10% profit.
4. Exit Condition: Exit the test trade or the full position when the daily
close drops below the 150-day EMA.

Output:
At the end of the backtest, display key trade statistics, including entry
exits, total returns, and risk metrics.
"""

class ScaledDailyStrategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        """
        Initialize scaled daily swing trading strategy

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.test_trade_amount = initial_investment * 0.10  # 10% for test trade
        self.full_trade_amount = initial_investment * 0.90  # 90% for scaling in

        # Initialize EMAs
        self.ema10 = EMA(10)    # 10-day EMA for entry
        self.ema200 = EMA(200)  # 200-day EMA for entry
        self.ema150 = EMA(150)  # 150-day EMA for exit

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

        # Calculate EMAs
        ema10_values = []
        ema200_values = []
        ema150_values = []

        for price in closes:
            self.ema10.push(price)
            self.ema200.push(price)
            self.ema150.push(price)
            ema10_values.append(self.ema10.get_ema())
            ema200_values.append(self.ema200.get_ema())
            ema150_values.append(self.ema150.get_ema())

        # Trading state variables
        in_test_trade = False
        in_scaled_trade = False
        test_entry_date = None
        test_entry_price = None
        scaled_entry_date = None
        scaled_entry_price = None

        # Start checking for trades after all EMAs have enough data
        start_idx = 200  # Start after longest EMA has enough data

        for i in range(start_idx, len(closes)):
            current_price = closes[i]
            current_date = dates[i]

            # Skip if we don't have valid EMA values
            if not all([ema10_values[i], ema200_values[i], ema150_values[i]]):
                continue

            # Check exit conditions first (close below 150 EMA)
            if (in_test_trade or in_scaled_trade) and \
                current_price < ema200_values[i]:

                # Exit test trade if active
                if in_test_trade:
                    print(f"Exiting test trade - Entry: {test_entry_date.strftime('%Y-%m-%d')} "
                          f"at {test_entry_price:.2f}, Exit: {current_date.strftime('%Y-%m-%d')} "
                          f"at {current_price:.2f}")
                    self.test_trades.append(Trade(
                        entry_date=test_entry_date,
                        entry_price=test_entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_test_trade = False

                # Exit scaled trade if active
                if in_scaled_trade:
                    print(f"Exiting scaled trade - Entry: {scaled_entry_date.strftime('%Y-%m-%d')} "
                          f"at {scaled_entry_price:.2f}, Exit: {current_date.strftime('%Y-%m-%d')} "
                          f"at {current_price:.2f}")
                    self.scaled_trades.append(Trade(
                        entry_date=scaled_entry_date,
                        entry_price=scaled_entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_scaled_trade = False

                continue

            # Entry conditions for test trade
            if not in_test_trade and not in_scaled_trade:
                # Check if close ≥ 10 EMA ≥ 200 EMA
                if (current_price >= ema10_values[i] and
                    ema10_values[i] >= ema200_values[i]):

                    in_test_trade = True
                    test_entry_date = current_date
                    test_entry_price = current_price
                    print(f"Entering test trade at {current_date.strftime('%Y-%m-%d')} "
                          f"price: {current_price:.2f}")

            # Check scaling conditions if in test trade
            elif in_test_trade and not in_scaled_trade:
                test_trade_profit = ((current_price - test_entry_price) / test_entry_price) * 100
                if test_trade_profit >= 10:  # Scale in if test trade is up 10%
                    in_scaled_trade = True
                    scaled_entry_date = current_date
                    scaled_entry_price = current_price
                    print(f"Scaling in at {current_date.strftime('%Y-%m-%d')} "
                          f"price: {current_price:.2f} (Test trade profit: {test_trade_profit:.2f}%)")

        # Close any open trades at the end
        if in_test_trade:
            self.test_trades.append(Trade(
                entry_date=test_entry_date,
                entry_price=test_entry_price,
                exit_date=dates[-1],
                exit_price=closes[-1]
            ))

        if in_scaled_trade:
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
    """Example usage of the scaled daily swing trading strategy"""
    strategy = ScaledDailyStrategy("../indices_data/nifty_midcap_50.csv",
                                 initial_investment=1000000)
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