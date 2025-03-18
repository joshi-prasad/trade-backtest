import os
import pandas as pd
from datetime import datetime


class MomentumInvesting:
    def __init__(self, directory_path):
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
        # df['12M_Return'] = self.calculate_returns(df, 52)

        # We are processing weekly data
        # So, we will calculate the EMA for 2, 4, 10, 20, 30, 40 weeks
        for ema in [2, 4, 10, 20, 30, 40]:
            df[f'{ema}EMA'] = df['Close'].ewm(span=ema, adjust=False).mean()

        return df

    def calculate_percentile_ranks(self):
        if not self.all_stocks_data:
            print("No stock data available for ranking.")
            return

        combined_df = pd.concat(
            self.all_stocks_data.values(),
            keys=self.all_stocks_data.keys(),
            names=['Ticker', 'Date'])

        for period in ['1M_Return', '3M_Return', '6M_Return']:
            combined_df[f'{period[:-7]}_Rank'] = combined_df.groupby(
                'Date')[period].rank(pct=True) * 100

        combined_df['RS_Rating'] = \
            (0.35 * combined_df['1M_Rank']) + \
            (0.33 * combined_df['3M_Rank']) + \
            (0.31 * combined_df['6M_Rank'])
        self.combined_data = combined_df

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
            for ema in [2, 4, 10, 20, 30, 40]
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

    def backtest_strategy_equity_only(self):
        available_weeks = self.retrieve_available_weeks()
        assert available_weeks, "No data available for analysis."

        capital = self.initial_capital
        previous_available_capital = capital
        portfolio = {}
        trade_count = 0

        # Iterate for each month
        for week in available_weeks[::2]:
            print(f"Processing week {week}...")
            available_capital = previous_available_capital

            # Get the top 10 stocks by RS Rating
            top_stocks = self.top_stocks_by_rs_rating(week, top_n=10)
            if top_stocks.empty:
                continue

            # Rebalanceing the portfolio

            sold = []
            # First iterate over the stocks to sell
            for ticker, quantity in portfolio.items():
                # Check if the stock is in the top 10
                if ticker in top_stocks.index.get_level_values('Ticker'):
                    continue
                stock_value = self.stock_value_lookup(week, ticker)
                assert stock_value is not None, "Stock value should not be None." + ticker
                available_capital += quantity * stock_value
                trade_count += 1
                # Remove the stock from the portfolio
                sold.append(ticker)
            for ticker in sold:
                del portfolio[ticker]

            # Now check if a stock in portfolio has allocation more than 20%
            # If yes, then bring allocation to 20%
            for ticker, quantity in portfolio.items():
                stock_value = self.stock_value_lookup(week, ticker)
                # print(f"--> Stock Value = {stock_value}, Quantity = {quantity}, ticker = {ticker}")
                if (quantity * stock_value) <= (capital * 0.2):
                    continue
                available_capital += quantity * stock_value - capital * 0.2
                trade_count += 1
                # update the portfolio with 20% allocation
                portfolio[ticker] = capital * 0.2 // stock_value


            # Now iterate over the top stocks to buy
            count = 0
            for ticker in top_stocks.index.get_level_values('Ticker'):
                stock_value = self.stock_value_lookup(week, ticker)
                if stock_value is None:
                    assert False, "Stock value should not be None."
                    continue

                # # If the stock is already in the portfolio, carry it forward
                # if ticker in portfolio:
                #     continue

                # Allocate equal capital to new stocks
                allocation = available_capital / (len(top_stocks) - count)
                quantity = allocation // stock_value
                if quantity == 0 or quantity < 0:
                    continue
                # print(f"ZERO StockValue={stock_value}"
                #     f",Quantity={quantity}"
                #     f",ticker={ticker}"
                #     f",available_capital={available_capital}"
                #     f",allocation={allocation}")
                # assert quantity > 0, "Quantity should be greater than 0."
                if ticker in portfolio:
                    portfolio[ticker] += quantity
                else:
                    portfolio[ticker] = quantity
                available_capital -= quantity * stock_value
                trade_count += 1
                count += 1

            previous_available_capital = available_capital

            # Print current portfolio
            print(f"\nPortfolio for week {week}:")
            invested_capital = 0
            for ticker, quantity in portfolio.items():
                stock_value = self.stock_value_lookup(week, ticker)
                assert stock_value is not None, "Stock value should not be None."
                invested_capital += quantity * stock_value
                print(f"{ticker}: {quantity} shares @ {stock_value} each")
            print(f"Available Capital: {available_capital}")
            print(f"Invested Capital: {invested_capital}")
            print(f"Total Capital: {invested_capital + available_capital}")

        # Liquidate portfolio at the end of the backtest
        for ticker, quantity in portfolio.items():
            stock_value = self.stock_value_lookup(available_weeks[-1], ticker)
            if stock_value is not None:
                capital += quantity * stock_value
                trade_count += 1

        # Calculate performance metrics
        final_capital = capital + previous_available_capital
        total_trades = trade_count
        cagr = self.calculate_cagr(
            self.initial_capital, final_capital, len(available_weeks))

        print(f"\nBacktest Results:")
        print(f"Initial Capital: {self.initial_capital}")
        print(f"Final Capital: {final_capital}")
        print(f"Total Trades: {total_trades}")
        print(f"Total Investment Period: {len(available_weeks) // 52} years")
        print(f"CAGR: {cagr}%")

    def calculate_cagr(self, initial_investment, final_value, total_weeks):
        years = total_weeks / 52
        cagr = ((final_value / initial_investment) ** (1 / years) - 1) * 100
        return cagr

    def backtest_asset_allocation(self):
        available_weeks = self.retrieve_available_weeks()
        assert available_weeks, "No data available for analysis."

        capital = self.initial_capital
        available_cash = capital
        invested_capital = 0
        portfolio = {}
        gold_invested_quantity = 0
        trade_count = 0
        kTotalStocksInPortfolio = 10

        # Iterate for each month
        for week in available_weeks[::2]:
            print(f"\nProcessing week {week}...")
            # Step 0: Compute total available capital for investment assuming
            # we sold everything
            for ticker, quantity in portfolio.items():
                stock_value = self.stock_value_lookup(week, ticker)
                available_cash += quantity * stock_value
                trade_count += 1
            portfolio = {}
            # Step 0a: Update the gold investment value
            gold_current_value = self.stock_value_lookup(week, 'GOLDBEES')
            available_cash += (gold_invested_quantity * gold_current_value)
            gold_invested_quantity = 0

            available_capital = available_cash

            # Find total stocks above EMA
            stocks_above_ema = self.stocks_above_ema(week)
            if not stocks_above_ema:
                continue
            # total stocks above 40 EMA
            # 2, 4, 10, 20, 30, 40
            above_200ema = stocks_above_ema.get('20EMA', 0)
            if (above_200ema is None) or (above_200ema <= 0):
                continue
            assert above_200ema, "No stocks above 40EMA."

            # Step 1: Get the top 10 stocks by RS Rating
            top_stocks = self.top_stocks_by_rs_rating(week, top_n=kTotalStocksInPortfolio)
            if top_stocks.empty:
                continue

            # Step 2: Sell the lagging stocks
            # Step 3: Compute the investment value
            equity_investment_value = 0
            sold = []
            for ticker, quantity in portfolio.items():
                stock_value = self.stock_value_lookup(week, ticker)

                # Check if the stock is in the top 10
                if ticker in top_stocks.index.get_level_values('Ticker'):
                    equity_investment_value += quantity * stock_value
                    continue
                stock_value = self.stock_value_lookup(week, ticker)
                available_capital += quantity * stock_value
                trade_count += 1
                # Remove the stock from the portfolio
                sold.append(ticker)
            for ticker in sold:
                del portfolio[ticker]

            # Step 3a: Find value of gold
            gold_current_value = self.stock_value_lookup(week, 'GOLDBEES')
            gold_invested_value = gold_invested_quantity * gold_current_value

            # Step 3b: Find total investment value
            investment_value = \
                equity_investment_value + \
                gold_invested_value + \
                available_capital

            # Step 4: Compute the allocation
            if above_200ema >= 70:
                # Allocate 70% to equity
                percentage_equity_allocation = 80
                expected_equity_allocation = 0.80 * investment_value
                expected_gold_allocation = 0.20 * investment_value
                print("Strong uptrend")
            elif above_200ema >= 40:
                # Allocate 50% to equity
                percentage_equity_allocation = 50
                expected_equity_allocation = 0.50 * investment_value
                expected_gold_allocation = 0.50 * investment_value
                print("Moderate uptrend")
            else:
                # Allocate 30% to equity
                percentage_equity_allocation = 30
                expected_equity_allocation = 0.30 * investment_value
                expected_gold_allocation = 0.70 * investment_value
                print("Weak uptrend")

            # Step 5: Rebalance the equity portfolio
            allocation_per_stock = expected_equity_allocation / len(top_stocks)
            # Step 5a: Sell stocks if allocation is more than 20%
            equity_sold_value = 0
            for ticker, quantity in portfolio.items():
                stock_value = self.stock_value_lookup(week, ticker)
                if (quantity * stock_value) <= (expected_equity_allocation * 0.20):
                    continue
                equity_sold_value += quantity * stock_value - expected_equity_allocation * 0.20
                trade_count += 1
                # update the portfolio with 20% allocation
                portfolio[ticker] = expected_equity_allocation * 0.20 // stock_value
            # Step 5b: Compute the available capital for equity investment
            equity_investment_value -= equity_sold_value
            available_capital_for_equity_investment = expected_equity_allocation - equity_investment_value
            # Step 5c: Buy new stocks
            if available_capital_for_equity_investment > 0:
                print(len(top_stocks))
                assert (len(top_stocks) >= kTotalStocksInPortfolio), "Too less stocks."
                count = 0
                for ticker in top_stocks.index.get_level_values('Ticker'):
                    print(f"Available Capital for Equity Investment: {available_capital_for_equity_investment}, count: {count}")
                    stock_value = self.stock_value_lookup(week, ticker)
                    assert (stock_value is not None), "Stock value should not be None."
                    # Allocate equal capital to new stocks
                    allocation = available_capital_for_equity_investment / (len(top_stocks) - count)
                    count += 1
                    assert allocation > 0, "Allocation should be greater than 0."
                    quantity = allocation // stock_value
                    assert quantity > 0, "Quantity should be greater than 0."
                    if ticker in portfolio:
                        if portfolio[ticker] >= quantity:
                            continue
                        to_buy = quantity - portfolio[ticker]
                        available_capital_for_equity_investment -= to_buy * stock_value
                        portfolio[ticker] += to_buy
                    else:
                        portfolio[ticker] = quantity
                        available_capital_for_equity_investment -= quantity * stock_value
                print("Equity Portfolio = ", portfolio)
                print(top_stocks)
                assert (len(portfolio) >= kTotalStocksInPortfolio), "Too less stocks."

            # Step 5d: Update the available cash
            available_cash = available_capital_for_equity_investment

            # Step 6: Rebalance the gold portfolio
            expected_gold_quantity = expected_gold_allocation // gold_current_value
            gold_invested_quantity = expected_gold_quantity

            # Print current portfolio
            print(f"\nPortfolio for week {week}:")
            print(f"Equity Allocation: {percentage_equity_allocation}% Gold Allocation: {100 - percentage_equity_allocation}%")
            invested_capital = 0
            assert len(portfolio) >= kTotalStocksInPortfolio, "Too less stocks."
            for ticker, quantity in portfolio.items():
                stock_value = self.stock_value_lookup(week, ticker)
                assert (stock_value is not None), "Stock value should not be None."
                invested_capital += quantity * stock_value
                print(f"{ticker}: {quantity} shares @ {stock_value} each")
            print(f"Available Capital: {available_cash}")
            print(f"Equity Invested Capital: {invested_capital}")
            print(f"Equity Total Capital: {invested_capital + available_cash}")
            print(f"Gold: {gold_invested_quantity * gold_current_value}")
            print(f"Total Capital: {invested_capital + available_cash + gold_invested_quantity * gold_current_value}")

        # Liquidate portfolio at the end of the backtest
        final_capital = 0
        for ticker, quantity in portfolio.items():
            stock_value = self.stock_value_lookup(available_weeks[-1], ticker)
            if stock_value is not None:
                final_capital += (quantity * stock_value)
                trade_count += 1
        final_capital += (self.stock_value_lookup(available_weeks[-1], 'GOLDBEES') * gold_invested_quantity)
        trade_count += 1

        # Calculate performance metrics
        total_trades = trade_count
        cagr = self.calculate_cagr(
            self.initial_capital, final_capital, len(available_weeks))

        print(f"\nBacktest Results:")
        print(f"Initial Capital: {self.initial_capital}")
        print(f"Final Capital: {final_capital}")
        print(f"Total Trades: {total_trades}")
        print(f"Total Investment Period: {len(available_weeks) // 52} years")
        print(f"CAGR: {cagr}%")


# Example usage
if __name__ == "__main__":
    directory_path = '../stock_data/'
    momentum_investing = MomentumInvesting(directory_path)
    momentum_investing.initialize()
    momentum_investing.backtest_asset_allocation()
