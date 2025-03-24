import os
import pandas as pd
from datetime import datetime


class MomentumInvesting:
    def __init__(self, directory_path):
        self.kWeeklyEMA = [2, 4, 10, 20, 30, 40]
        self.directory_path = directory_path
        self.all_stocks_data = {}
        self.combined_data = None
        self.initial_capital = 1000000
        self.portfolio = {}
        self.trade_log = []

    def read_csv_files_from_directory(self):
        return [f for f in os.listdir(self.directory_path) if f.endswith('.csv')]

    def calculate_returns(self, df, period):
        if len(df) < period:
            return pd.Series([None] * len(df), index=df.index)
        return df['Close'].pct_change(periods=period)

    def process_stock_data(self, file_path):
        print("Processing", file_path)
        df = pd.read_csv(file_path)

        if 'Date' not in df.columns or 'Close' not in df.columns:
            print(f"Skipping {file_path} due to missing 'Date' or 'Close' column.")
            return None

        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.date
        df.set_index('Date', inplace=True)

        # Perform calculations
        df['1M_Return'] = self.calculate_returns(df, 4)
        df['3M_Return'] = self.calculate_returns(df, 12)
        df['6M_Return'] = self.calculate_returns(df, 24)
        df['12M_Return'] = self.calculate_returns(df, 52)

        # Calculate EMAs
        for ema in self.kWeeklyEMA:
            df[f'{ema}EMA'] = df['Close'].ewm(span=ema, adjust=False).mean()

        # Calculate rally percentages
        df['Rallied_60_12W'] = df['Close'].pct_change(periods=12) >= 0.60
        df['Rallied_30_6W'] = df['Close'].pct_change(periods=6) >= 0.30
        df['Rallied_15_3W'] = df['Close'].pct_change(periods=3) >= 0.15
        df['Rallied_10_2W'] = df['Close'].pct_change(periods=2) >= 0.10

        return df

    def calculate_percentile_ranks(self):
        if not self.all_stocks_data:
            print("No stock data available for ranking.")
            return

        combined_df = pd.concat(
            self.all_stocks_data.values(),
            keys=self.all_stocks_data.keys(),
            names=['Ticker', 'Date'])

        for period in ['1M_Return', '3M_Return', '6M_Return', '12M_Return']:
            combined_df[f'{period[:-7]}_Rank'] = combined_df.groupby(
                'Date')[period].rank(pct=True) * 100

        # 1 Month: 28%, 3 Month: 26%, 6 Month: 24%, 12 Month: 22%
        combined_df['RS_Rating'] = \
            (0.28 * combined_df['1M_Rank']) + \
            (0.26 * combined_df['3M_Rank']) + \
            (0.24 * combined_df['6M_Rank']) + \
            (0.22 * combined_df['12M_Rank'])
        self.combined_data = combined_df

    def calculate_rally_percentages(self):
        if self.combined_data is None:
            print("No data available for analysis.")
            return {}

        total_stocks = len(self.all_stocks_data)

        latest_data = self.combined_data.groupby('Date').apply(lambda x: pd.Series({
            'Rallied_60_12W': (x['Rallied_60_12W'].sum() / total_stocks) * 100,
            'Rallied_30_6W': (x['Rallied_30_6W'].sum() / total_stocks) * 100,
            'Rallied_15_3W': (x['Rallied_15_3W'].sum() / total_stocks) * 100,
            'Rallied_10_2W': (x['Rallied_10_2W'].sum() / total_stocks) * 100
        }))

        return latest_data

    def retrieve_available_weeks(self):
        if self.combined_data is None:
            return []

        weeks = self.combined_data.index.get_level_values('Date').unique().tolist()
        weeks.sort()
        return weeks

    def top_stocks_by_rs_rating(self, week, top_n=10):
        if self.combined_data is not None:
            latest_data = self.combined_data.xs(week, level='Date')
            top_stocks = latest_data.nlargest(top_n, 'RS_Rating')
            return top_stocks[['RS_Rating', '1M_Return', '3M_Return', '6M_Return']]
        return pd.DataFrame()

    def stock_value_lookup(self, week, ticker):
        if self.combined_data is None:
            print("No data available for analysis.")
            return None
        try:
            stock_data = self.combined_data.xs(
                (ticker, week), level=('Ticker', 'Date'))
            if stock_data.empty:
                print(f"No data available for {ticker} in week {week}.")
                return None
            return float(stock_data['Close'].iloc[0])
        except KeyError or ValueError:
            return None

    def stocks_above_ema(self, week):
        if self.combined_data is None or \
            week not in self.retrieve_available_weeks():
            return {}

        latest_data = self.combined_data.xs(week, level='Date')

        return {
            f'{ema}EMA': (latest_data['Close'] > latest_data[f'{ema}EMA']).sum()
            for ema in self.kWeeklyEMA
        }

    def initialize(self):
        # List of CSV files in the directory
        csv_files = self.read_csv_files_from_directory()

        # Process each CSV file
        for csv_file in csv_files:
            ticker = csv_file.split('.')[0]
            file_path = os.path.join(self.directory_path, csv_file)
            stock_data = self.process_stock_data(file_path)
            self.all_stocks_data[ticker] = stock_data

        # Calculate percentile ranks and RS Rating
        self.calculate_percentile_ranks()

    def backtest_asset_allocation(self):
        available_weeks = self.retrieve_available_weeks()
        assert available_weeks, "No data available for analysis."

        capital = self.initial_capital
        available_cash = capital
        invested_capital = 0
        portfolio = {}
        gold_invested_quantity = 0
        kTotalStocksInPortfolio = 10

        # Iterate for each month
        for week in available_weeks[::2]:
            print(f"\nProcessing week {week}...")
            # Step 1: Assume all protfolio is sold and compute available cash
            equity_cash = self.sell_all_stocks(week, portfolio, available_cash)
            gold_cash = self.compute_gold_investment_value(
                week, gold_invested_quantity)
            available_cash = equity_cash + gold_cash
            gold_invested_quantity = 0
            portfolio = {}

            # Step 2: Check if total stocks above 20 week EMA to find strong,
            # moderate or weak uptrend
            stocks_above_ema = self.stocks_above_ema(week)
            if not stocks_above_ema:
                continue

            # Step 3: Check if total stocks above 20 week EMA
            above_20ema = stocks_above_ema.get('20EMA', 0)
            if (above_20ema is None) or (above_20ema <= 0):
                continue
            assert above_20ema, "No stocks above 20EMA."
            percentage_equity_allocation, \
                expected_equity_allocation, \
                expected_gold_allocation = self.compute_allocation(
                    above_20ema, available_cash)

            # Step 4: Find top stocks by RS Rating
            top_stocks = self.top_stocks_by_rs_rating(
                week, top_n=kTotalStocksInPortfolio)
            if top_stocks.empty:
                continue

            # Step 5: Buy gold
            gold_current_value = self.stock_value_lookup(week, 'GOLDBEES')
            gold_invested_quantity = \
                expected_gold_allocation // gold_current_value
            gold_invested_value = gold_invested_quantity * gold_current_value

            # Step 6: Rebalance equity portfolio
            portfolio, available_cash = self.rebalance_equity_portfolio(
                week, top_stocks, expected_equity_allocation)

            # Step 7: Print portfolio
            self.print_portfolio(
                week,
                portfolio,
                available_cash,
                gold_invested_quantity,
                gold_current_value,
                percentage_equity_allocation)

        final_capital = self.liquidate_portfolio(
            available_weeks, portfolio, gold_invested_quantity)

        self.print_backtest_results(final_capital, 0, len(available_weeks))

    def sell_all_stocks(self, week, portfolio, available_cash):
        for ticker, quantity in portfolio.items():
            stock_value = self.stock_value_lookup(week, ticker)
            assert stock_value, f"No data available for {ticker} in week {week}."
            available_cash += quantity * stock_value
        return available_cash

    def compute_gold_investment_value(self, week, gold_invested_quantity):
        gold_current_value = self.stock_value_lookup(week, 'GOLDBEES')
        assert gold_current_value, f"No data available for GOLDBEES in week {week}."
        return gold_invested_quantity * gold_current_value

    def rebalance_portfolio(self, week, top_stocks, portfolio, available_cash):
        equity_investment_value = 0
        sold = []
        for ticker, quantity in portfolio.items():
            stock_value = self.stock_value_lookup(week, ticker)
            if ticker in top_stocks.index.get_level_values('Ticker'):
                equity_investment_value += quantity * stock_value
                continue
            available_cash += quantity * stock_value
            sold.append(ticker)
        for ticker in sold:
            del portfolio[ticker]
        return equity_investment_value, available_cash, portfolio

    def compute_allocation(self, above_20ema, investment_value):
        if above_20ema >= 70:
            percentage_equity_allocation = 80
            expected_equity_allocation = 0.80 * investment_value
            expected_gold_allocation = 0.20 * investment_value
            print("Trend: Strong uptrend")
        elif above_20ema >= 40:
            percentage_equity_allocation = 50
            expected_equity_allocation = 0.50 * investment_value
            expected_gold_allocation = 0.50 * investment_value
            print("Trend: Moderate uptrend")
        else:
            percentage_equity_allocation = 30
            expected_equity_allocation = 0.30 * investment_value
            expected_gold_allocation = 0.70 * investment_value
            print("Trend: Weak uptrend")
        return percentage_equity_allocation, \
            expected_equity_allocation, \
            expected_gold_allocation

    def rebalance_equity_portfolio(
        self, week, top_stocks, expected_equity_allocation):

        portfolio = {}
        available_capital_for_equity_investment = expected_equity_allocation
        count = 0
        for ticker in top_stocks.index.get_level_values('Ticker'):
            stock_value = self.stock_value_lookup(week, ticker)
            assert stock_value, f"No data available for {ticker} in week {week}."
            allocation = available_capital_for_equity_investment / (len(top_stocks) - count)
            quantity = allocation // stock_value
            assert quantity, f"Quantity for {ticker} is 0."
            portfolio[ticker] = quantity
            available_capital_for_equity_investment -= quantity * stock_value
            count += 1
        available_cash = available_capital_for_equity_investment
        return portfolio, available_cash

    def rebalance_gold_portfolio(
            self, expected_gold_allocation, gold_current_value):
        expected_gold_quantity = expected_gold_allocation // gold_current_value
        return expected_gold_quantity

    def print_portfolio(
        self,
        week,
        portfolio,
        available_cash,
        gold_invested_quantity,
        gold_current_value,
        percentage_equity_allocation):

        print(f"\nPortfolio for week {week}:")
        print(f"Equity Allocation: {percentage_equity_allocation}% Gold Allocation: {100 - percentage_equity_allocation}%")
        invested_capital = 0
        total_stocks = len(portfolio)
        for ticker, quantity in portfolio.items():
            stock_value = self.stock_value_lookup(week, ticker)
            assert stock_value, f"No data available for {ticker} in week {week}."
            invested_capital += quantity * stock_value
            print(f"{ticker}: {100/total_stocks:2.0f}% of portfolio @ {stock_value} each")
        # print(f"Available Cash: {available_cash:.1f}")
        # print(f"Equity Invested Capital: {invested_capital:.1f}")
        # print(f"Equity Total Capital: {invested_capital + available_cash:.1f}")
        # print(f"Gold Investment: {gold_invested_quantity * gold_current_value:.1f}")
        # print(f"Total Capital: {invested_capital + available_cash + gold_invested_quantity * gold_current_value:.1f}")

    def liquidate_portfolio(self, available_weeks, portfolio, gold_invested_quantity):
        final_capital = 0
        for ticker, quantity in portfolio.items():
            stock_value = self.stock_value_lookup(available_weeks[-1], ticker)
            if stock_value is not None:
                final_capital += (quantity * stock_value)
        final_capital += (self.stock_value_lookup(available_weeks[-1], 'GOLDBEES') * gold_invested_quantity)
        return final_capital

    def print_backtest_results(self, final_capital, trade_count, total_weeks):
        total_trades = trade_count
        cagr = self.calculate_cagr(
            self.initial_capital, final_capital, total_weeks)
        print(f"\nBacktest Results:")
        print(f"Initial Capital: {self.initial_capital:.1f}")
        print(f"Final Capital: {final_capital:.1f}")
        print(f"Total Trades: {total_trades}")
        print(f"Total Investment Period: {total_weeks // 52} years")
        print(f"CAGR: {cagr:.2f}%")

    def calculate_cagr(self, initial_investment, final_value, total_weeks):
        years = total_weeks / 52
        cagr = ((final_value / initial_investment) ** (1 / years) - 1) * 100
        return cagr


# Example usage
if __name__ == "__main__":
    directory_path = '../stock_data/'
    momentum_investing = MomentumInvesting(directory_path)
    momentum_investing.initialize()
    momentum_investing.backtest_asset_allocation()
