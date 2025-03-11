"""
What is RSI (Relative Strength Index)?
RSI is a momentum oscillator that measures the speed and magnitude of price
changes. It oscillates between 0 and 100 and is typically used to identify
overbought or oversold conditions in a traded security.

RSI values:
1. Above 70: Typically indicates overbought conditions
2. Below 30: Typically indicates oversold conditions
3. 50: Centerline, often used to identify trend direction

RSI Calculation:
1. Calculate average gains and losses over N periods
2. Calculate Relative Strength (RS) = Average Gain / Average Loss
3. RSI = 100 - (100 / (1 + RS))
"""

class RSI:
    def __init__(self, period: int = 14):
        """
        Initialize RSI calculator

        Args:
            period (int): Number of periods for RSI calculation (default: 14)
        """
        self.period = period
        self.prev_close = None
        self.gains = []  # List to store price gains
        self.losses = []  # List to store price losses
        self.avg_gain = None  # Average gain over period
        self.avg_loss = None  # Average loss over period
        self.rsi_value = None

    def _calculate_change(self, close: float) -> tuple[float, float]:
        """
        Calculate price change and determine gain/loss

        Args:
            close: Current closing price

        Returns:
            tuple[float, float]: (gain, loss) values
        """
        if self.prev_close is None:
            self.prev_close = close
            return 0.0, 0.0

        change = close - self.prev_close
        self.prev_close = close

        if change > 0:
            return change, 0.0
        else:
            return 0.0, abs(change)

    def push(self, close: float) -> float:
        """
        Add new price data and calculate RSI

        Args:
            close: Current period's closing price

        Returns:
            float: Current RSI value if available, None otherwise
        """
        gain, loss = self._calculate_change(close)
        self.gains.append(gain)
        self.losses.append(loss)

        # Keep only the needed number of periods
        if len(self.gains) > self.period:
            self.gains.pop(0)
            self.losses.pop(0)

        # Calculate RSI when we have enough data
        if len(self.gains) == self.period:
            if self.avg_gain is None:
                # First RSI uses simple averages
                self.avg_gain = sum(self.gains) / self.period
                self.avg_loss = sum(self.losses) / self.period
            else:
                # Subsequent values use smoothed averages
                self.avg_gain = ((self.avg_gain * (self.period - 1)) + gain) / self.period
                self.avg_loss = ((self.avg_loss * (self.period - 1)) + loss) / self.period

            # Calculate RS and RSI
            if self.avg_loss == 0:
                self.rsi_value = 100.0
            else:
                rs = self.avg_gain / self.avg_loss
                self.rsi_value = 100 - (100 / (1 + rs))

        return self.rsi_value

    def get_rsi(self) -> float:
        """
        Get the current RSI value

        Returns:
            float: Current RSI value if available, None otherwise
        """
        return self.rsi_value

    def is_overbought(self, threshold: float = 70.0) -> bool:
        """
        Check if current RSI indicates overbought conditions

        Args:
            threshold: RSI threshold for overbought condition (default: 70.0)

        Returns:
            bool: True if overbought, False otherwise
        """
        if self.rsi_value is None:
            return False
        return self.rsi_value >= threshold

    def is_oversold(self, threshold: float = 30.0) -> bool:
        """
        Check if current RSI indicates oversold conditions

        Args:
            threshold: RSI threshold for oversold condition (default: 30.0)

        Returns:
            bool: True if oversold, False otherwise
        """
        if self.rsi_value is None:
            return False
        return self.rsi_value <= threshold