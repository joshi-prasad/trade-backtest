from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
Swing trading strategy based on weekly charts, focusing exclusively on long
trades.

Strategy Rules
1. Initial Test Trade: Enter a long position using 10% of the total available
investment.
2. Entry for test trade: condition: Weekly close ≥ 2-week EMA ≥ 40-week EMA.
3. Scaling In: Invest the remaining 90% only if the initial test trade achieves
at least 10% profit.
4. Exit Condition: Exit the test trade or the full position when the weekly
close drops below the 40-week EMA.

Output:
At the end of the backtest, display key trade statistics, including entry
exits, total returns, and risk metrics.
"""

class ScaledWeeklyStrategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        """
        Initialize scaled weekly swing trading strategy

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.test_trade_amount = initial_investment * 0.10  # 10% for test trade
        self.full_trade_amount = initial_investment * 0.90  # 90% for scaling in

        # Initialize EMAs for weekly timeframe
        self.ema2w = EMA(2)  # 2-week EMA
        self.ema40w = EMA(40)  # 40-week EMA

        self.trades: List[Trade] = []
        self.test_trades: List[Trade] = []  # Keep track of test trades separately
        self.scaled_trades: List[Trade] = []  # Keep track of scaled-in trades

    def _convert_to_weekly(self, daily_data: Dict[str, List[Any]]) -> pd.DataFrame:
        """Convert daily data to weekly data using pandas"""
        df = pd.DataFrame({
            'open': daily_data['open'],
            'high': daily_data['high'],
            'low': daily_data['low'],
            'close': daily_data['close'],
            'shares_traded': daily_data['shares_traded'],
            'turnover': daily_data['turnover']
        }, index=daily_data['dates'])

        weekly = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'shares_traded': 'sum',
            'turnover': 'sum'
        })

        return weekly

    def run(self) -> Tuple[StrategyStats, Dict[str, StrategyStats]]:
        """
        Run the strategy and return statistics

        Returns:
            Tuple containing:
            - Overall strategy statistics
            - Dictionary with separate statistics for test and scaled trades
        """
        # Read and convert data
        daily_data = self.reader.get_data_as_lists()
        weekly_data = self._convert_to_weekly(daily_data)

        # Get weekly prices and dates
        weekly_closes = weekly_data['close'].values
        dates = weekly_data.index

        # Calculate EMAs
        ema2w_values = []
        ema40w_values = []

        for price in weekly_closes:
            self.ema2w.push(price)
            self.ema40w.push(price)
            ema2w_values.append(self.ema2w.get_ema())
            ema40w_values.append(self.ema40w.get_ema())

        # Trading state variables
        in_test_trade = False
        in_scaled_trade = False
        test_entry_date = None
        test_entry_price = None
        scaled_entry_date = None
        scaled_entry_price = None

        # Start checking for trades after both EMAs have enough data
        start_idx = 40  # Start after EMA40 has enough data

        for i in range(start_idx, len(weekly_closes)):
            current_price = weekly_closes[i]
            current_date = dates[i]

            # Skip if we don't have valid EMA values
            if not ema2w_values[i] or not ema40w_values[i]:
                continue

            # Check exit conditions first
            if (in_test_trade or in_scaled_trade) and \
                current_price < ema40w_values[i]:

                # Exit test trade if active
                if in_test_trade:
                    self.test_trades.append(Trade(
                        entry_date=test_entry_date,
                        entry_price=test_entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_test_trade = False

                # Exit scaled trade if active
                if in_scaled_trade:
                    self.scaled_trades.append(Trade(
                        entry_date=scaled_entry_date,
                        entry_price=scaled_entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_scaled_trade = False

                continue

            # Entry conditions
            if not in_test_trade and not in_scaled_trade:
                # Check entry conditions for test trade
                if (current_price > ema2w_values[i] and
                    ema2w_values[i] > ema40w_values[i]):

                    in_test_trade = True
                    test_entry_date = current_date
                    test_entry_price = current_price

            # Check if test trade meets scaling criteria
            elif in_test_trade and not in_scaled_trade:
                test_trade_profit = ((current_price - test_entry_price) / test_entry_price) * 100.0
                if test_trade_profit >= 10.0:  # Scale in if test trade is up 10%
                    in_scaled_trade = True
                    scaled_entry_date = current_date
                    scaled_entry_price = current_price

        # Close any open trades at the end
        if in_test_trade:
            self.test_trades.append(Trade(
                entry_date=test_entry_date,
                entry_price=test_entry_price,
                exit_date=dates[-1],
                exit_price=weekly_closes[-1]
            ))

        if in_scaled_trade:
            self.scaled_trades.append(Trade(
                entry_date=scaled_entry_date,
                entry_price=scaled_entry_price,
                exit_date=dates[-1],
                exit_price=weekly_closes[-1]
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
    """Example usage of the scaled weekly swing trading strategy"""
    strategy = ScaledWeeklyStrategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000)
    overall_stats, detailed_stats = strategy.run()

    print("\nOverall Strategy Performance:")
    print("===========================")
    print(overall_stats)

    print("\nTest Trades Performance:")
    print("=====================")
    print(detailed_stats['test_trades'])

    print("\nScaled Trades Performance:")
    print("=======================")
    print(detailed_stats['scaled_trades'])

if __name__ == "__main__":
    main()