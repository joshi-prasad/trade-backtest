from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from index_csv_reader import IndexCSVReader
from adx import ADX
from ema import EMA
from strategy_stats import Trade, StrategyStats
from rolling_high_low_tracker import RollingHighLowTracker
from boolean_lookback_counter import BooleanLookbackCounter
from base_count import BaseCounter

class Strategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.current_investment = initial_investment
        self.max_loss = 2.0

        self.ema5 = EMA(5)
        self.ema10 = EMA(10)
        self.ema21 = EMA(21)
        self.ema51 = EMA(51)
        self.ema150 = EMA(150)
        self.ema200 = EMA(200)
        self.adx = ADX(14)
        self.base_counter = BaseCounter()

        self.ema5_value = None
        self.ema10_value = None
        self.ema21_value = None
        self.ema51_value = None
        self.ema150_value = None
        self.ema200_value = None
        self.adx_value = None
        self.base_count = 0

        self.trades: List[Trade] = []

        self.entry_price = None
        self.entry_date = None
        self.stop_loss_price = None
        self.sl_hit = False

        # True if a close below 51MA is a condition for exit
        self.use_51ma_stop_loss = True
        self.exit_reason = None

        self.reset_state()

    def reset_state(self):
        self.ema5_value = None
        self.ema10_value = None
        self.ema21_value = None
        self.ema51_value = None
        self.ema150_value = None
        self.ema200_value = None
        self.base_count = 0

        self.adx_value = None
        self.entry_price = None
        self.entry_date = None
        self.stop_loss_price = None
        self.use_51ma_stop_loss = True
        self.exit_reason = None
        self.sl_hit = False

    def should_exit_trade(
        self,
        date: datetime,
        close: float,
        low: float) -> bool:
        """ check if we should exit the trade """
        ma5 = self.ema5_value
        ma10 = self.ema10_value
        ma21 = self.ema21_value
        ma51 = self.ema51_value
        if low <= self.stop_loss_price:
            self.exit_reason = "SL"
            self.sl_hit = True
            return True
        if self.base_counter.is_base_counting():
            if self.base_counter.get_base_count() <= 2:
                if close < self.ema200_value:
                    self.exit_reason = "Below 200MA"
                    return True
            else:
                if close < self.ema51_value:
                    self.exit_reason = "Below 51MA"
                    return True
            return False
        if self.use_51ma_stop_loss:
            if close < ma51:
                self.exit_reason = "Below 51MA"
                return True
        else:
            if close < ma10:
                self.exit_reason = "Below 10MA"
                return True
        return False

    def should_enter_trade(
        self,
        high: float,
        low: float,
        close: float,
        yesterday_low: float,
        yesterday_close: float) -> bool:
        """ check if we should enter the trade """

        ma5 = self.ema5_value
        adx = self.adx_value

        todays_range = high - low
        top_75_percent = low + todays_range * 0.75
        if (yesterday_close > ma5 and
            low >= ma5 and
            close > ma5 and
            adx >= 15) and (
                close >= top_75_percent or
                close > yesterday_close):
            return True
        return False

    def exit_trade(self, exit_date: datetime, exit_price: float):

        """ exit the trade """
        entry_date = self.entry_date
        entry_price = self.entry_price

        pl_percent = ((exit_price - entry_price) / entry_price) * 100
        qunatity = self.current_investment / entry_price
        pl = qunatity * (exit_price - entry_price)
        self.current_investment = qunatity * exit_price

        self.trades.append(
            Trade(entry_date, entry_price, exit_date, exit_price)
        )
        print(f"EntryDate={entry_date.strftime('%Y-%m-%d')}"
            f",EntryPrice={entry_price:.2f}"
            f",ExitDate={exit_date.strftime('%Y-%m-%d')}"
            f",ExitPrice={exit_price:.2f}"
            f",PL={pl:.0f}"
            f",PL%={pl_percent:.2f}%"
            f",HoldingDays={(exit_date - entry_date).days}"
            f",ExitReason={self.exit_reason}"
            # f",BaseCount={self.base_counter.get_base_count()},"
            # f",PriceSL={self.stop_loss_price:.2f},"
            # f",51maSL: {self.use_51ma_stop_loss}"
        )
        pass

    def should_move_stop_loss(
        self,
        close: float) -> Tuple[bool, float]:
        """ check if we should move the stop loss """
        # move the stop loss to the entry price if the current profit is more
        # than 2%
        if self.stop_loss_price > self.entry_price:
            return (False, None)
        profit = (close - self.entry_price) / self.entry_price
        if profit > 0.05:
            return (True, self.entry_price)
        return (False, None)

    def run(self) -> Tuple[StrategyStats, Dict[str, StrategyStats]]:
        # Read data
        data = self.reader.get_data_as_lists()
        dates = data['dates']
        closes = data['close']
        lows = data['low']
        high = data['high']

        # Calculate MAs
        ma5_values = []
        ma10_values = []
        ma21_values = []
        ma51_values = []
        ma150_values = []
        ma200_values = []

        for price in closes:
            ma5_values.append(self.ema5.push(price))
            ma10_values.append(self.ema10.push(price))
            ma21_values.append(self.ema21.push(price))
            ma51_values.append(self.ema51.push(price))
            ma150_values.append(self.ema150.push(price))
            ma200_values.append(self.ema200.push(price))

        # Trading state variables
        in_trade = False
        entry_date = None
        entry_price = None

        consecutive_loss = 0
        trade_cool_off = 0
        disable_cool_off = False
        display_logs = False
        for i in range(0, len(closes)):
            # display_logs = (len(self.trades) == 41)
            # Get current values
            date = dates[i]
            today_close = closes[i]
            today_low = lows[i]
            today_high = high[i]
            yesterday_close = closes[i-1]
            yesterday_low = lows[i-1]

            (adx, plus_di, minus_di) = self.adx.push(
                high = today_high,
                low = today_low,
                close = today_close)

            if trade_cool_off > 0 and not disable_cool_off:
                trade_cool_off -= 1
                continue

            # Skip if we don't have valid values
            if not all([adx,
                ma5_values[i],
                ma10_values[i],
                ma21_values[i],
                ma51_values[i],
                ma150_values[i],
                ma200_values[i]]):
                continue

            # Update state variables
            self.ema5_value = ma5_values[i]
            self.ema10_value = ma10_values[i]
            self.ema21_value = ma21_values[i]
            self.ema51_value = ma51_values[i]
            self.ema150_value = ma150_values[i]
            self.ema200_value = ma200_values[i]
            self.adx_value = adx
            self.base_count = self.base_counter.get_base_count()

            self.base_counter.push(
                date = date,
                price = today_close,
                ema50 = self.ema51_value,
                ema150 = self.ema150_value,
                ema200 = self.ema200_value
            )

            if in_trade:
                (move, stop_loss) = self.should_move_stop_loss(
                    close = today_close)
                if move:
                    # Fixed stop loss
                    self.stop_loss_price = stop_loss

                # Use 51MA as stop loss once the price is above it
                if not self.use_51ma_stop_loss:
                    self.use_51ma_stop_loss = (
                        today_close >= self.ema51_value and
                        self.ema5_value > self.ema51_value)
                if display_logs:
                    print(f"Date={date},"
                        f"51MA SL={self.use_51ma_stop_loss},"
                        f"IsBaseCounting={self.base_counter.is_base_counting()},"
                        f"BaseCount={self.base_counter.get_base_count()}"
                    )

                # Check if we should exit the trade
                if not self.should_exit_trade(date, today_close, today_low):
                    continue

                # Exit the trade
                in_trade = False
                exit_price = today_close
                if self.sl_hit:
                    exit_price = self.stop_loss_price
                self.exit_trade(
                    exit_date = date, exit_price = exit_price)
                profit_percent = ((today_close - self.entry_price) / self.entry_price) * 100
                holding_days = (date - self.entry_date).days
                if (profit_percent < 1.0):
                    # Assume profit less than 4% is a loss
                    # Increase consecutive loss count
                    # If consecutive loss is more than 3, more cool off time
                    consecutive_loss += 1
                    if consecutive_loss >= 3:
                        trade_cool_off = 10
                else:
                    # Reset consecutive loss count
                    consecutive_loss = 0
                    if (profit_percent > 50 or holding_days > 200):
                        # If profit is more than 30%, more cool off time
                        trade_cool_off = 10
                    else:
                        trade_cool_off = 0

                # Reset state variables
                self.reset_state()
                continue


            # Check if we should enter a trade
            if not self.should_enter_trade(
                high = today_high,
                low = today_low,
                close = today_close,
                yesterday_low = yesterday_low,
                yesterday_close = yesterday_close):
                continue

            # Enter the trade
            in_trade = True
            self.entry_date = date
            self.entry_price = today_close
            self.stop_loss_price = self.entry_price - (self.entry_price * self.max_loss / 100)
            self.use_51ma_stop_loss = (today_close >= self.ema51_value and self.ema5_value > self.ema51_value)

        # Calculate stats
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