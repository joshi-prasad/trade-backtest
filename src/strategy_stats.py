from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from collections import defaultdict

@dataclass
class Trade:
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float

    @property
    def holding_period(self) -> int:
        """Return holding period in days"""
        return (self.exit_date - self.entry_date).days

    @property
    def profit_pct(self) -> float:
        """Return profit percentage"""
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100

class YearlyStats:
    """Class to hold statistics for a single year"""
    def __init__(self, year: int):
        self.year = year
        self.trades: List[Trade] = []
        self.profitable_trades: List[Trade] = []
        self.losing_trades: List[Trade] = []
        self.total_trades = 0
        self.win_rate = 0
        self.loss_rate = 0
        self.avg_profit = 0
        self.avg_loss = 0
        self.total_profit = 0
        self.total_loss = 0
        self.net_profit = 0

    def calculate_stats(self):
        """Calculate statistics for the year"""
        self.total_trades = len(self.trades)
        self.profitable_trades = [t for t in self.trades if t.profit_pct > 0]
        self.losing_trades = [t for t in self.trades if t.profit_pct <= 0]

        # Calculate rates
        self.win_rate = (len(self.profitable_trades) / self.total_trades * 100) if self.total_trades > 0 else 0
        self.loss_rate = (len(self.losing_trades) / self.total_trades * 100) if self.total_trades > 0 else 0

        # Calculate profits and losses
        profitable_pcts = [t.profit_pct for t in self.profitable_trades]
        losing_pcts = [t.profit_pct for t in self.losing_trades]

        self.avg_profit = np.mean(profitable_pcts) if profitable_pcts else 0
        self.avg_loss = np.mean(losing_pcts) if losing_pcts else 0
        self.total_profit = sum(profitable_pcts) if profitable_pcts else 0
        self.total_loss = sum(losing_pcts) if losing_pcts else 0
        self.net_profit = self.total_profit + self.total_loss

    def __str__(self) -> str:
        return f"""
Year {self.year}:
-------------
Total Trades: {self.total_trades}
Win Rate: {self.win_rate:.2f}%
Loss Rate: {self.loss_rate:.2f}%
Average Profit: {self.avg_profit:.2f}%
Average Loss: {self.avg_loss:.2f}%
Total Profit: {self.total_profit:.2f}%
Total Loss: {self.total_loss:.2f}%
Net Profit: {self.net_profit:.2f}%
"""

class StrategyStats:
    def __init__(self, trades: List[Trade], initial_investment: float = 100000):
        """
        Initialize strategy statistics calculator

        Args:
            trades: List of Trade objects
            initial_investment: Initial capital for trading (default: 100,000)
        """
        self.trades = sorted(trades, key=lambda x: x.entry_date)
        self.initial_investment = initial_investment
        self.yearly_stats: Dict[int, YearlyStats] = {}
        self._calculate_stats()

    def _calculate_yearly_stats(self):
        """Calculate statistics broken down by year"""
        # Group trades by year
        trades_by_year = defaultdict(list)
        for trade in self.trades:
            year = trade.entry_date.year
            trades_by_year[year].append(trade)

        # Calculate stats for each year
        for year, year_trades in trades_by_year.items():
            yearly_stat = YearlyStats(year)
            yearly_stat.trades = year_trades
            yearly_stat.calculate_stats()
            self.yearly_stats[year] = yearly_stat

    def _calculate_trading_periods(self):
        """Calculate days in trade and out of trade"""
        # Calculate total days in trade
        self.days_in_trade = sum(trade.holding_period for trade in self.trades)

        # Calculate days out of trade (gaps between trades)
        self.days_out_of_trade = 0
        for i in range(1, len(self.trades)):
            prev_trade_exit = self.trades[i-1].exit_date
            current_trade_entry = self.trades[i].entry_date
            gap_days = (current_trade_entry - prev_trade_exit).days
            if gap_days > 0:  # Only count positive gaps
                self.days_out_of_trade += gap_days

        # Calculate total period
        if self.trades:
            self.total_days = (self.trades[-1].exit_date - self.trades[0].entry_date).days + 1
            self.pct_time_in_trade = (self.days_in_trade / self.total_days * 100) if self.total_days > 0 else 0
            self.years_invested = self.total_days / 365.25  # Use 365.25 to account for leap years
        else:
            self.total_days = 0
            self.pct_time_in_trade = 0
            self.years_invested = 0

    def _calculate_investment_returns(self):
        """Calculate investment-based returns"""
        current_capital = self.initial_investment
        self.total_gain = 0
        self.total_loss = 0

        # Calculate trade-by-trade P&L
        for trade in self.trades:
            profit_amount = current_capital * (trade.profit_pct / 100)
            current_capital += profit_amount

            if profit_amount > 0:
                self.total_gain += profit_amount
            else:
                self.total_loss += abs(profit_amount)

        self.final_capital = current_capital
        self.net_profit = self.final_capital - self.initial_investment
        self.total_return_pct = ((self.final_capital / self.initial_investment) - 1) * 100

        # Calculate CAGR
        if self.years_invested > 0:
            self.cagr = (pow(self.final_capital / self.initial_investment, 1/self.years_invested) - 1) * 100
        else:
            self.cagr = 0

    def _calculate_stats(self):
        """Calculate all strategy statistics"""
        # Calculate yearly statistics
        self._calculate_yearly_stats()

        # Calculate trading periods
        self._calculate_trading_periods()

        # Calculate investment returns
        self._calculate_investment_returns()

        self.total_trades = len(self.trades)

        # Separate profitable and losing trades
        self.profitable_trades = [t for t in self.trades if t.profit_pct > 0]
        self.losing_trades = [t for t in self.trades if t.profit_pct <= 0]

        # Basic trade stats
        self.num_profitable = len(self.profitable_trades)
        self.num_losing = len(self.losing_trades)
        self.win_rate = (self.num_profitable / self.total_trades) * 100 if self.total_trades > 0 else 0

        # Profit statistics
        all_profits = [t.profit_pct for t in self.trades]
        self.max_profit = max(all_profits) if all_profits else 0
        self.max_loss = min(all_profits) if all_profits else 0
        self.avg_profit = np.mean(all_profits) if all_profits else 0
        self.profit_std = np.std(all_profits) if all_profits else 0

        # Calculate maximum drawdown
        self.max_drawdown = self._calculate_max_drawdown()

        # Holding periods
        profitable_periods = [t.holding_period for t in self.profitable_trades]
        losing_periods = [t.holding_period for t in self.losing_trades]

        self.avg_holding_profitable = np.mean(profitable_periods) if profitable_periods else 0
        self.avg_holding_losing = np.mean(losing_periods) if losing_periods else 0

        # Additional metrics
        self.profit_factor = self._calculate_profit_factor()
        self.sharpe_ratio = self._calculate_sharpe_ratio()

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if not self.trades:
            return 0

        equity_curve = self._generate_equity_curve()
        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = (running_max - equity_curve) / running_max * 100
        return np.max(drawdowns)

    def _generate_equity_curve(self) -> np.ndarray:
        """Generate equity curve starting from initial investment"""
        equity = self.initial_investment
        curve = [equity]

        for trade in self.trades:
            equity *= (1 + trade.profit_pct/100)
            curve.append(equity)

        return np.array(curve)

    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        return self.total_gain / self.total_loss if self.total_loss != 0 else float('inf')

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio assuming risk-free rate of 2%"""
        if not self.trades:
            return 0
        risk_free_rate = 2  # 2% annual
        excess_returns = [t.profit_pct - (risk_free_rate/252) for t in self.trades]  # daily adjustment
        if not excess_returns:
            return 0
        return np.mean(excess_returns) / (np.std(excess_returns) if np.std(excess_returns) != 0 else 1) * np.sqrt(252)

    def __str__(self) -> str:
        """Return formatted statistics string"""
        base_stats = f"""
Overall Strategy Statistics:
=========================
Investment Analysis:
-----------------
Initial Investment: ₹{self.initial_investment:,.2f}
Final Capital: ₹{self.final_capital:,.2f}
Total Gain: ₹{self.total_gain:,.2f}
Total Loss: ₹{self.total_loss:,.2f}
Net Profit/Loss: ₹{self.net_profit:,.2f}
Total Return: {self.total_return_pct:.2f}%
CAGR: {self.cagr:.2f}%

Time Analysis:
------------
Total Period: {self.total_days} days ({self.years_invested:.1f} years)
Days in Trade: {self.days_in_trade} days
Days out of Trade: {self.days_out_of_trade} days
Percentage Time in Trade: {self.pct_time_in_trade:.2f}%

Trade Statistics:
---------------
Total Trades: {self.total_trades}
Profitable Trades: {self.num_profitable}
Losing Trades: {self.num_losing}
Win Rate: {self.win_rate:.2f}%

Profit Metrics:
-------------
Maximum Profit: {self.max_profit:.2f}%
Maximum Loss: {self.max_loss:.2f}%
Average Profit: {self.avg_profit:.2f}%
Profit Std Dev: {self.profit_std:.2f}%
Maximum Drawdown: {self.max_drawdown:.2f}%
Profit Factor: {self.profit_factor:.2f}

Time Metrics:
-----------
Avg Holding (Profitable): {self.avg_holding_profitable:.1f} days
Avg Holding (Losing): {self.avg_holding_losing:.1f} days

Risk Metrics:
-----------
Sharpe Ratio: {self.sharpe_ratio:.2f}

Annual Performance Breakdown:
========================="""

        # Add yearly statistics
        yearly_stats = ""
        for year in sorted(self.yearly_stats.keys()):
            yearly_stats += str(self.yearly_stats[year])

        return base_stats + yearly_stats