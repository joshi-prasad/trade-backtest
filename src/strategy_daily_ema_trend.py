from typing import List, Dict, Any
from datetime import datetime
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
Swing Trading Strategy (Daily Chart) - Long Trades Only
This strategy focuses on long trades, leveraging exponential moving averages
(EMAs) for trend confirmation and risk management.

Entry Conditions: Enter a long position when both of the following conditions are met:
1. Today's low > 5-day EMA > 10-day EMA (indicating strong upward momentum).
2. Yesterday's close > 5-day EMA (confirming sustained strength).

Exit Conditions: Exit the trade under either of the following circumstances:
1. Loss exceeds 5% (to limit downside risk).
2. When 20MA is below 200MA. a close below 20MA causes the long trade to exit.
3. When 20MA is above 200MA. a close below 200MA will cause the trade exit.

"""

class TrendEmaStrategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        """
        Initialize trend following EMA strategy

        Args:
            file_path: Path to the CSV file containing index data
            initial_investment: Initial capital for trading
        """
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.max_loss_pct = 5.0  # Maximum allowed loss
        self.cooling_period = 0  # Days to wait after stop loss

        # Initialize EMAs
        self.ema5 = EMA(5)    # 5-day EMA for entry
        self.ema10 = EMA(10)  # 10-day EMA for entry
        self.ema20 = EMA(20)  # 20-day EMA for exit
        self.ema200 = EMA(200)  # 200-day EMA for exit

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
        lows = data['low']

        # Calculate EMAs
        ema5_values = []
        ema10_values = []
        ema20_values = []
        ema200_values = []

        for price in closes:
            self.ema5.push(price)
            self.ema10.push(price)
            self.ema20.push(price)
            self.ema200.push(price)
            ema5_values.append(self.ema5.get_ema())
            ema10_values.append(self.ema10.get_ema())
            ema20_values.append(self.ema20.get_ema())
            ema200_values.append(self.ema200.get_ema())

        # Trading state variables
        in_trade = False
        entry_date = None
        entry_price = None
        cooling_off_until = None  # Index until which we should avoid trading

        # Start checking for trades after all EMAs have enough data
        start_idx = 200  # Start after longest EMA has enough data

        for i in range(start_idx, len(closes)):
            current_price = closes[i]
            current_date = dates[i]
            current_low = lows[i]

            # Skip if we don't have valid EMA values
            if not all([
                ema5_values[i],
                ema10_values[i],
                ema20_values[i],
                ema200_values[i]]):
                continue

            if in_trade:
                # Calculate current profit/loss
                current_profit = (
                    (current_price - entry_price) / entry_price) * 100

                # Check exit conditions
                exit_triggered = False
                exit_reason = ""
                # Flag to track if exit was due to stop loss
                stop_loss_exit = False

                # 1. Stop loss check
                if current_profit <= -self.max_loss_pct:
                    exit_triggered = True
                    stop_loss_exit = True
                    exit_reason = f"Stop loss triggered "
                        f"at {current_profit:.2f}%"

                # 2. & 3. MA-based exit conditions
                elif ema20_values[i] < ema200_values[i]:
                    # When 20MA is below 200MA, exit on close below 20MA
                    if current_price < ema20_values[i]:
                        exit_triggered = True
                        exit_reason = "Price closed below 20MA (20MA < 200MA)"
                else:
                    # When 20MA is above 200MA, exit on close below 200MA
                    if current_price < ema200_values[i]:
                        exit_triggered = True
                        exit_reason = "Price closed below 200MA (20MA > 200MA)"

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

                    # If stop loss was hit, set cooling off period
                    if stop_loss_exit:
                        cooling_off_until = i + self.cooling_period
                        print(f"Entering cooling-off period until: {
                            dates[min(
                                cooling_off_until,
                                len(dates)-1)].strftime('%Y-%m-%d')}")

            else:
                # Skip if we're in cooling-off period
                if cooling_off_until is not None and i < cooling_off_until:
                    continue

                # Check entry conditions
                # 1. Today's low > 5EMA > 10EMA
                # 2. Yesterday's close > 5EMA
                if (current_low > ema5_values[i] and
                    ema5_values[i] > ema10_values[i] and
                    closes[i-1] > ema5_values[i-1]):

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
    """Example usage of the trend EMA strategy"""
    strategy = TrendEmaStrategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000
    )
    stats = strategy.run()

    print("\nTrend EMA Strategy Results:")
    print("=========================")
    print(stats)

if __name__ == "__main__":
    main()