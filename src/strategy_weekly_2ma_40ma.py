from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

class WeeklySwingStrategy:
    def __init__(self, file_path: str):
        """
        Initialize weekly swing trading strategy

        Args:
            file_path (str): Path to the CSV file containing index data
        """
        self.reader = IndexCSVReader(file_path)
        self.data = None
        self.trades: List[Trade] = []

        # Initialize EMAs for weekly timeframe
        self.ema2w = EMA(2)  # 2-week EMA
        self.ema40w = EMA(40)  # 40-week EMA

    def _convert_to_weekly(self, daily_data: Dict[str, List[Any]]) -> pd.DataFrame:
        """
        Convert daily data to weekly data using pandas

        Args:
            daily_data: Dictionary containing daily price data

        Returns:
            pd.DataFrame: Weekly OHLC data with dates as index
        """
        # Create pandas DataFrame from daily data
        df = pd.DataFrame({
            'open': daily_data['open'],
            'high': daily_data['high'],
            'low': daily_data['low'],
            'close': daily_data['close'],
            'shares_traded': daily_data['shares_traded'],
            'turnover': daily_data['turnover']
        }, index=daily_data['dates'])

        # Resample to weekly data
        weekly = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'shares_traded': 'sum',
            'turnover': 'sum'
        })

        return weekly

    def run(self) -> StrategyStats:
        """
        Run the strategy and return statistics

        Returns:
            StrategyStats: Computed strategy statistics
        """
        # Read daily data
        daily_data = self.reader.get_data_as_lists()

        # Convert to weekly
        weekly_data = self._convert_to_weekly(daily_data)

        # Calculate weekly EMAs
        weekly_closes = weekly_data['close'].values
        dates = weekly_data.index

        ema2w_values = []
        ema40w_values = []

        for price in weekly_closes:
            self.ema2w.push(price)
            self.ema40w.push(price)
            ema2w_values.append(self.ema2w.get_ema())
            ema40w_values.append(self.ema40w.get_ema())

        # Look for trading opportunities
        in_trade = False
        entry_date = None
        entry_price = None

        # Start checking for trades after both EMAs have enough data
        start_idx = 40  # Start after EMA40 has enough data

        for i in range(start_idx, len(weekly_closes)):
            current_price = weekly_closes[i]
            current_date = dates[i]

            # Skip if we don't have valid EMA values
            if not ema2w_values[i] or not ema40w_values[i]:
                assert False, f"EMA values are not valid for date: {current_date}"
                continue

            if not in_trade:
                # Check entry conditions:
                # 1. Close above 2-week EMA
                # 2. 2-week EMA above 40-week EMA
                if (current_price > ema2w_values[i] and
                    ema2w_values[i] > ema40w_values[i]):

                    in_trade = True
                    entry_date = current_date
                    entry_price = current_price

            else:
                # Check exit condition:
                # Close below 40-week EMA
                if current_price < ema40w_values[i]:
                    # Exit the trade
                    print(f"Entry date: {entry_date}, "
                        f"Entry price: {entry_price}, "
                        f"Exit date: {current_date}, "
                        f"Exit price: {current_price}")
                    self.trades.append(Trade(
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_trade = False

        # Close any open trade at the end of the period
        if in_trade:
            self.trades.append(Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=dates[-1],
                exit_price=weekly_closes[-1]
            ))

        # Calculate and return statistics
        return StrategyStats(self.trades, initial_investment=1000000)

def main():
    """Example usage of the weekly swing trading strategy"""
    # Initialize and run strategy
    strategy = WeeklySwingStrategy("../indices_data/nifty_midcap_50.csv")
    stats = strategy.run()

    # Print statistics
    print("\nWeekly Swing Strategy Results:")
    print("============================")
    print(stats)

if __name__ == "__main__":
    main()