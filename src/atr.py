"""
What is ATR (Average True Range)?
ATR (Average True Range) measures market volatility by calculating the average
range of price movement over a period (e.g., 14 days). It does not indicate
trend direction, only how much the price fluctuates.

ATR values:
1. High ATR -> High volatility (big price movements).
2. Low ATR -> Low volatility (whipsaw risk).

ATR helps set stop losses and detect whipsaws.
"""

class ATR:
    def __init__(self, period: int = 14):
        """
        Initialize ATR calculator

        Args:
            period (int): Number of periods for ATR calculation (default: 14)
        """
        self.period = period
        self.true_ranges = []
        self.atr_value = None
        self.prev_close = None

    def _calculate_true_range(self, high: float, low: float, close: float) -> float:
        """
        Calculate True Range for a single period

        True Range is the greatest of:
        1. Current High - Current Low
        2. |Current High - Previous Close|
        3. |Current Low - Previous Close|

        Args:
            high: Current period's high price
            low: Current period's low price
            close: Current period's closing price

        Returns:
            float: True Range value
        """
        if self.prev_close is None:
            tr = high - low  # First period only uses high-low range
        else:
            tr = max(
                high - low,  # Current period range
                abs(high - self.prev_close),  # High-Previous Close
                abs(low - self.prev_close)    # Low-Previous Close
            )

        self.prev_close = close
        return tr

    def push(self, high: float, low: float, close: float) -> float:
        """
        Add new price data and calculate ATR

        Args:
            high: Current period's high price
            low: Current period's low price
            close: Current period's closing price

        Returns:
            float: Current ATR value if available, None otherwise
        """
        tr = self._calculate_true_range(high, low, close)
        self.true_ranges.append(tr)

        # Keep only the needed number of periods
        if len(self.true_ranges) > self.period:
            self.true_ranges.pop(0)

        # Calculate ATR using Wilder's smoothing
        if len(self.true_ranges) == self.period:
            if self.atr_value is None:
                # First ATR is simple average of TR
                self.atr_value = sum(self.true_ranges) / self.period
            else:
                # Subsequent ATRs use Wilder's smoothing
                self.atr_value = ((self.atr_value * (self.period - 1)) + tr) / self.period

        return self.atr_value

    def get_atr(self) -> float:
        """
        Get the current ATR value

        Returns:
            float: Current ATR value if available, None otherwise
        """
        return self.atr_value