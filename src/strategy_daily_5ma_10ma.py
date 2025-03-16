from typing import List, Dict, Any, Tuple
from datetime import datetime
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats
from rolling_high_low_tracker import RollingHighLowTracker
from boolean_lookback_counter import BooleanLookbackCounter

"""
Long-Only Strategy for Backtesting on a Daily Chart

Entry Conditions:
1. Today's low is greater than the 5-day EMA, which is also greater than the
10-day EMA.
2. Yesterday's close is above the 5-day EMA.

Exit Conditions:
1. If the price closes below the 10-day EMA and the daily decline is greater
than 5%, exit the trade at the day's close price.
2. If the price closes below the 10-day EMA but the decline is less than 5%,
track the day's close as a low marker:
a. If the price closes below this low marker within the next two days, exit
the trade.
b. If the price does not close below this low marker within the next two days,
reset the low marker and continue holding the position.
"""

class Strategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.max_loss_pct = 5.0  # Maximum allowed loss for scaled position

        self.ema5 = EMA(5)
        self.ema10 = EMA(10)

        self._enter_trade_above_lookback_high = True
        self.high_low_tracker = RollingHighLowTracker(10)
        self.month_high_low_tracker = RollingHighLowTracker(20)

        # Total times the price crossed above the 5 Day EMA in last 20 days
        self._capture_total_ma_crosses = True
        self.ma5_cross = BooleanLookbackCounter(10)
        self.ma10_cross = BooleanLookbackCounter(10)

        self.low_marker = None # For tracking the low marker
        self.low_marker_date = None # For tracking the low marker date

        self.exit_reason = ""  # Reason for exiting the trade

        self.test_trades: List[Trade] = []
        self.test_trade_amount = initial_investment * 0.01

        self.trades: List[Trade] = []
        self.scaled_trade_amount = initial_investment * 0.99

    def should_exit_trade(
        self,
        day: int,
        current_price: float,
        entry_price: float,
        ma5: float,
        ma10: float) -> bool:
        """
        Check if the strategy should exit a trade

        Exit Conditions:
        1. If the price closes below the 10-day EMA and the daily decline is
        greater than 5%, exit the trade at the day's close price.
        2. If the price closes below the 10-day EMA but the decline is less
        than 5%, track the day's close as a low marker:
            a. If the price closes below this low marker within the next two
            days, exit the trade.
            b. If the price does not close below this low marker within the
            next two days, reset the low marker and continue holding the
            position.
        """

        # Check if price is above 10-day EMA
        if current_price >= ma10:
            # Reset low marker if price is above 10-day EMA
            self.low_marker = None
            self.low_marker_date = None
            return False

        # Check if price decline is greater than max loss percentage
        price_change = (current_price - entry_price) / entry_price * 100
        if price_change < -self.max_loss_pct:
            # Exit trade if price decline is greater than max loss percentage
            self.exit_reason = "SL-HIT"
            return True

        # Check if low marker is set
        if self.low_marker:
            # Check if price closes below low marker
            if current_price < self.low_marker:
                # Exit trade if price closes below low marker
                self.exit_reason = "LOW-MARKER"
                return True
            if day - self.low_marker_date >= 2:
                # Reset low marker if price has not closed below it
                # within 2 days
                self.low_marker = None
                self.low_marker_date = None
        else:
            # Set low marker if not already set
            self.low_marker = current_price
            self.low_marker_date = day
        return False

    def should_enter_trade(
        self,
        current_price: float,
        current_low: float,
        yesterday_close: float,
        ma5: float,
        ma10: float,
        lookback_high: float) -> bool:
        """
        Check if the strategy should enter a trade  (long-only)
        Entry Conditions:
        1. Today's low is greater than the 5-day EMA, which is also greater
        than the 10-day EMA.
        2. Yesterday’s close is above the 5-day EMA.
        """
        if not self._enter_trade_above_lookback_high:
            if (current_low > ma5 and
                ma5 > ma10 and
                yesterday_close > ma5):
                return True
        else:
            if (current_low > ma5 and
                ma5 > ma10 and
                yesterday_close > ma5 and
                current_price >= lookback_high):
                return True
        return False

    def exit_trade(
        self,
        entry_date: datetime,
        entry_price: float,
        exit_date: datetime,
        exit_price: float,
        entry_ma5_crosses: int,
        entry_ma10_crosses: int):
        """ Exit the trade and update statistics """
        self.trades.append(Trade(
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=exit_date,
            exit_price=exit_price
        ))
        print(f"Entry: {entry_date.strftime('%Y-%m-%d')} at {entry_price:.2f}"
            f" Exit: {exit_date.strftime('%Y-%m-%d')} at {exit_price:.2f}"
            f" Profit: {((exit_price - entry_price) / entry_price) * 100:.2f}%"
            f" Holding: {exit_date - entry_date} days"
            f" MA5 Crosses: {entry_ma5_crosses} "
            f" MA10 Crosses: {entry_ma10_crosses}"
            f" Reason: {self.exit_reason}")

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
        lows = data['low']

        # Calculate MAs
        ma5_values = []
        ma10_values = []
        recent_highs = []
        recent_lows = []
        monthly_highs = []
        monthly_lows = []
        is_price_below_5ma = False
        is_price_below_10ma = False

        for price in closes:
            self.ema5.push(price)
            self.ema10.push(price)
            ma5_values.append(self.ema5.get_ema())
            ma10_values.append(self.ema10.get_ema())
            (low, high) = self.high_low_tracker.push(price)
            recent_highs.append(high)
            recent_lows.append(low)
            (low, high) = self.month_high_low_tracker.push(price)
            monthly_highs.append(high)
            monthly_lows.append(low)

        # Trading state variables
        in_trade = False
        entry_date = None
        entry_price = None
        entry_ma5_crosses = None
        entry_ma10_crosses = None

        # Start checking for trades after all MAs have enough data
        start_idx = 10  # Start after longest MA has enough data

        for i in range(start_idx, len(closes)):
            current_price = closes[i]
            current_date = dates[i]
            current_low = lows[i]

            # Skip if we don't have valid values
            if not all(
                [ma5_values[i],
                ma10_values[i],
                recent_highs[i],
                monthly_highs[i]]):
                continue

            cureent_ma5 = ma5_values[i]
            current_ma10 = ma10_values[i]
            lookback_high = recent_highs[i]
            monthly_high = monthly_highs[i]

            # Capture total times the price crossed above the 5 Day EMA in
            # last 20 days
            v = False
            if current_low < cureent_ma5:
                v = (is_price_below_5ma == False)
                is_price_below_5ma = True
            else:
                is_price_below_5ma = False
            self.ma5_cross.push(v)

            # Capture total times the price crossed above the 10 Day EMA in
            # last 20 days
            v = False
            if current_low < current_ma10:
                v = (is_price_below_10ma == False)
                is_price_below_10ma = True
            else:
                is_price_below_10ma = False
            self.ma10_cross.push(v)

            ma5_crosses = self.ma5_cross.count_true()
            ma10_crosses = self.ma10_cross.count_true()

            # Check exit conditions first
            if in_trade:
                # Check for exit conditions
                if self.should_exit_trade(
                    day=i,
                    current_price=current_price,
                    entry_price=entry_price,
                    ma5=cureent_ma5,
                    ma10=current_ma10) == False:
                    # Continue holding the trade
                    continue

                # TODO: handle exit trade
                self.exit_trade(
                    entry_date,
                    entry_price,
                    current_date,
                    current_price,
                    entry_ma5_crosses,
                    entry_ma10_crosses
                )
                in_trade = False
                continue

            # Check entry conditions
            if (self.should_enter_trade(
                    current_price,
                    current_low,
                    closes[i - 1],
                    cureent_ma5,
                    current_ma10,
                    lookback_high) == False):
                    # No entry signal
                    continue

            # Enter trade
            entry_date = current_date
            entry_price = current_price
            entry_ma5_crosses = ma5_crosses
            entry_ma10_crosses = ma10_crosses
            in_trade = True

        # Calculate and return statistics
        return StrategyStats(self.trades, self.initial_investment)

def main():
    """Example usage of the trend EMA strategy"""
    strategy = Strategy(
        "../indices_data/nifty_midcap_50.csv",
        initial_investment=1000000
    )
    stats = strategy.run()

    print("\nStrategy Results:")
    print("=========================")
    print(stats)

if __name__ == "__main__":
    main()
