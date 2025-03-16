from typing import List, Dict, Any, Tuple
from datetime import datetime
from index_csv_reader import IndexCSVReader
from ema import EMA
from strategy_stats import Trade, StrategyStats

"""
Most optimal strategy for the given dataset

Trade Dates
-----------
1. 28 Aug 2013 to 7 July 2014
2. 29 Feb 2016 to 25 Oct 2016
3. 27 Dec 2016 to 8 Jan 2018
4. 24 Mar 2020 to 18 Oct 2021
5. 20 Jun 2022 to 14 Dec 2022
6. 28 Mar 2023 to 24 Sep 2024
"""

class Strategy:
    def __init__(self, file_path: str, initial_investment: float = 100000):
        self.reader = IndexCSVReader(file_path)
        self.initial_investment = initial_investment
        self.max_loss_pct = 5.0

        self.trade_dates = [
            (datetime(2013, 8, 28), datetime(2014, 7, 7)),
            (datetime(2016, 2, 29), datetime(2016, 10, 25)),
            (datetime(2016, 12, 27), datetime(2018, 1, 8)),
            (datetime(2020, 3, 24), datetime(2021, 10, 18)),
            (datetime(2022, 6, 20), datetime(2022, 12, 14)),
            (datetime(2023, 3, 28), datetime(2024, 9, 24))
        ]

        self.trades: List[Trade] = []

    def should_enter_trade(self, currnet_date: datetime) -> bool:
        """
        Check if the strategy should enter a trade
        """
        for start_date, end_date in self.trade_dates:
            if start_date == currnet_date:
                return True
        return False

    def should_exit_trade(self, currnet_date: datetime) -> bool:
        """
        Check if the strategy should exit a trade
        """
        for start_date, end_date in self.trade_dates:
            if end_date == currnet_date:
                return True
        return False

    def exit_trade(
        self,
        entry_date: datetime,
        entry_price: float,
        exit_date: datetime,
        exit_price: float):
        """ Exit the trade and update statistics """
        self.trades.append(Trade(
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=exit_date,
            exit_price=exit_price
        ))
        print(f"Entry: {entry_date.strftime('%Y-%m-%d')} at {entry_price:.2f}"
            f" Exit: {exit_date.strftime('%Y-%m-%d')} at {exit_price:.2f}"
            f" Profit: {((exit_price - entry_price) / entry_price) * 100:.2f}%")

    def run(self):
        # Read data
        data = self.reader.get_data_as_lists()
        dates = data['dates']
        closes = data['close']

        # Trading state variables
        in_trade = False
        entry_date = None
        entry_price = None

        for i in range(1, len(dates)):
            current_date = dates[i]
            current_price = closes[i]

            # Check if trade should be exited
            if in_trade:
                if self.should_exit_trade(current_date):
                    self.exit_trade(
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=current_date,
                        exit_price=current_price
                    )
                    in_trade = False
                continue

            # Check if trade should be entered
            if self.should_enter_trade(current_date):
                in_trade = True
                entry_date = current_date
                entry_price = current_price

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
