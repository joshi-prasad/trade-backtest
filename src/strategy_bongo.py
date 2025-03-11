from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from index_csv_reader import IndexCSVReader
from rsi import RSI
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
Bongo Strategy Implementation

Description:
This script implements the Bongo strategy for swing trading using weekly
charts.

The strategy is based on the relationship between multiple RSI values and an
EMA:

    - A "Blue Bongo" signal occurs when:
      RSI(8) > RSI(14) > RSI(19) and Close > EMA(9)
    - A "Red Bongo" signal occurs when:
      RSI(8) < RSI(14) < RSI(19) and Close < EMA(9)

Trading Rules:
    - Enter a long position when the Bongo turns Blue.
    - Exit the long position when the Bongo turns Red.

Strategy Execution:
    - The script processes weekly candlestick data.
    - It identifies buy and sell signals based on the Bongo criteria.
    - It tracks trade entries, exits, and calculates performance statistics.

Performance Metrics:
At the end of execution, the script prints key strategy statistics, including:
    - Total number of trades
    - Win rate percentage
    - Average gain/loss per trade
    - Maximum drawdown
    - Overall profitability

"""

class BongoStrategy:
    def __init__(self,
        file_path: str,
        initial_investment: float = 100000,
        weekly: bool = True):
        """
        Initialize Bongo strategy using multiple RSI periods and EMA

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.weekly = weekly
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment

        # Initialize indicators
        self.rsi8 = RSI(period=8)
        self.rsi14 = RSI(period=14)
        self.rsi19 = RSI(period=19)
        self.ema9 = EMA(9)

        self.trades: List[Trade] = []

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

    def _is_blue_bongo(self, rsi8: float, rsi14: float, rsi19: float,
                       close: float, ema9: float) -> bool:
        """Check if Bongo is Blue"""
        if None in (rsi8, rsi14, rsi19, ema9):
            return False
        return (rsi8 > rsi14) and (rsi14 > rsi19) and (close > ema9)

    def _is_red_bongo(self, rsi8: float, rsi14: float, rsi19: float,
                      close: float, ema9: float) -> bool:
        """Check if Bongo is Red"""
        if None in (rsi8, rsi14, rsi19, ema9):
            return False
        return (rsi8 < rsi14) and (rsi14 < rsi19) and (close < ema9)

    def run(self) -> StrategyStats:
        """
        Run the strategy and return statistics

        Returns:
            StrategyStats: Computed strategy statistics
        """
        # Read and convert data to weekly
        daily_data = self.reader.get_data_as_lists()

        if self.weekly:
            # Get weekly data series
            weekly_data = self._convert_to_weekly(daily_data)
            closes = weekly_data['close'].values
            dates = weekly_data.index
        else:
            dates = daily_data['dates']
            closes = daily_data['close']

        # Lists to store indicator values
        rsi8_values = []
        rsi14_values = []
        rsi19_values = []
        ema9_values = []

        # Trading state variables
        in_trade = False
        entry_date = None
        entry_price = None

        # Calculate indicators for each period
        for i in range(len(closes)):
            # Update indicators
            current_price = closes[i]
            current_date = dates[i]

            rsi8_value = self.rsi8.push(current_price)
            rsi14_value = self.rsi14.push(current_price)
            rsi19_value = self.rsi19.push(current_price)
            ema9_value = self.ema9.push(current_price)

            rsi8_values.append(rsi8_value)
            rsi14_values.append(rsi14_value)
            rsi19_values.append(rsi19_value)
            ema9_values.append(ema9_value)

            # Need enough data for all indicators
            if None in (rsi19_value, ema9_value):  # RSI19 needs most data
                continue

            if in_trade:
                # Check for exit (Red Bongo)
                if self._is_red_bongo(rsi8_value, rsi14_value, rsi19_value,
                                    current_price, ema9_value):
                    # Exit the trade
                    profit = ((current_price - entry_price) / entry_price) * 100
                    print(f"\nExiting trade (Red Bongo):")
                    print(f"Entry: {entry_date.strftime('%Y-%m-%d')} at {entry_price:.2f}")
                    print(f"Exit: {current_date.strftime('%Y-%m-%d')} at {current_price:.2f}")
                    print(f"Profit: {profit:.2f}%")

                    self.trades.append(Trade(
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_trade = False

            else:
                # Check for entry (Blue Bongo)
                if self._is_blue_bongo(rsi8_value, rsi14_value, rsi19_value,
                                     current_price, ema9_value):
                    in_trade = True
                    entry_date = current_date
                    entry_price = current_price
                    print(f"\nEntering trade (Blue Bongo):")
                    print(f"Entry date: {entry_date.strftime('%Y-%m-%d')}")
                    print(f"Entry price: {entry_price:.2f}")

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
    """Example usage of the Bongo strategy"""
    strategy = BongoStrategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000,
        weekly=False,
    )
    stats = strategy.run()

    print("\nBongo Strategy Results:")
    print("=====================")
    print(stats)

if __name__ == "__main__":
    main()