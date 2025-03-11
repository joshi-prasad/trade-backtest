from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
Swing Trading Strategy - Weekly Chart (Long Trades Only)
This strategy is designed for long trades, utilizing exponential moving
averages (EMAs) to confirm trends and manage risk effectively.

Entry Conditions:
Enter a long position when both of the following conditions are met:
1. This week's low > 2-week EMA > 4-week EMA (indicating strong upward
momentum).
2. Previous week's close > 2-week EMA (confirming sustained strength).

Exit Conditions
Exit the trade under any of the following conditions:
1. Loss exceeds 5% (to limit downside risk).
2. 4-week EMA drops below the 40-week EMA, and the price closes below the
4-week EMA (signaling a trend reversal).
3. 4-week EMA is above the 40-week EMA, but the price closes below the 40-week
EMA (indicating weakening momentum).
"""

class WeeklyTrendEmaStrategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        """
        Initialize weekly trend following EMA strategy

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.max_loss_pct = 5.0  # Maximum allowed loss

        # Initialize EMAs for weekly timeframe
        self.ema2w = EMA(2)    # 2-week EMA for entry
        self.ema4w = EMA(4)    # 4-week EMA for entry and exit
        self.ema40w = EMA(40)  # 40-week EMA for exit

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

    def run(self) -> StrategyStats:
        """
        Run the strategy and return statistics

        Returns:
            StrategyStats: Computed strategy statistics
        """
        # Read and convert data to weekly
        daily_data = self.reader.get_data_as_lists()
        weekly_data = self._convert_to_weekly(daily_data)

        # Get weekly data series
        closes = weekly_data['close'].values
        lows = weekly_data['low'].values
        dates = weekly_data.index

        # Calculate EMAs
        ema2w_values = []
        ema4w_values = []
        ema40w_values = []

        for price in closes:
            self.ema2w.push(price)
            self.ema4w.push(price)
            self.ema40w.push(price)
            ema2w_values.append(self.ema2w.get_ema())
            ema4w_values.append(self.ema4w.get_ema())
            ema40w_values.append(self.ema40w.get_ema())

        # Trading state variables
        in_trade = False
        entry_date = None
        entry_price = None

        # Start checking for trades after all EMAs have enough data
        start_idx = 40  # Start after longest EMA (40-week) has enough data

        for i in range(start_idx, len(closes)):
            current_price = closes[i]
            current_date = dates[i]
            current_low = lows[i]

            # Skip if we don't have valid EMA values
            if not all([ema2w_values[i], ema4w_values[i], ema40w_values[i]]):
                continue

            if in_trade:
                # Calculate current profit/loss
                current_profit = ((current_price - entry_price) / entry_price) * 100

                # Check exit conditions
                exit_triggered = False
                exit_reason = ""

                # 1. Stop loss check
                if current_profit <= -self.max_loss_pct:
                    exit_triggered = True
                    exit_reason = f"Stop loss triggered at {current_profit:.2f}%"

                # 2. & 3. EMA-based exit conditions
                elif ema4w_values[i] < ema40w_values[i]:
                    # When 4-week EMA is below 40-week EMA, exit on close below 4-week EMA
                    if current_price < ema4w_values[i]:
                        exit_triggered = True
                        exit_reason = "Price closed below 4-week EMA (4W < 40W)"
                else:
                    # When 4-week EMA is above 40-week EMA, exit on close below 40-week EMA
                    if current_price < ema40w_values[i]:
                        exit_triggered = True
                        exit_reason = "Price closed below 40-week EMA (4W > 40W)"

                if exit_triggered:
                    print(f"\nExiting trade ({exit_reason}):")
                    print(f"Entry: {entry_date.strftime('%Y-%m-%d')} at {entry_price:.2f}")
                    print(f"Exit: {current_date.strftime('%Y-%m-%d')} at {current_price:.2f}")
                    print(f"Profit: {current_profit:.2f}%")

                    self.trades.append(Trade(
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    ))
                    in_trade = False

            else:
                # Check entry conditions
                # 1. This week's low > 2W EMA > 4W EMA
                # 2. Previous week's close > 2W EMA
                if (current_low > ema2w_values[i] > ema4w_values[i] and
                    closes[i-1] > ema2w_values[i-1]):

                    in_trade = True
                    entry_date = current_date
                    entry_price = current_price
                    print(f"\nEntering trade:")
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
    """Example usage of the weekly trend EMA strategy"""
    strategy = WeeklyTrendEmaStrategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000
    )
    stats = strategy.run()

    print("\nWeekly Trend EMA Strategy Results:")
    print("================================")
    print(stats)

if __name__ == "__main__":
    main()