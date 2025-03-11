from typing import Tuple

"""
What is ADX (Average Directional Index)?
ADX (Average Directional Index) is a technical indicator that measures the
strength of a trend, but it does not indicate the direction of the trend.

ADX values:
1. Above 25 -> Strong trend (up or down).
2. Below 20 -> Weak or choppy market (possible whipsaw conditions).

Components of ADX:
1. +DI (Positive Directional Indicator): Measures the strength of upward
movement.
2. -DI (Negative Directional Indicator): Measures the strength of downward
movement.
3. ADX is derived from the difference between +DI and -DI.

ADX helps identify when to enter trend-based trades
"""

class ADX:
    def __init__(self, period: int = 14):
        """
        Initialize ADX calculator

        Args:
            period (int): Number of periods for ADX calculation (default: 14)
        """
        self.period = period
        self.prev_high = None
        self.prev_low = None

        # Lists to store directional movement
        self.plus_dm = []   # +DM values
        self.minus_dm = []  # -DM values
        self.tr = []        # True Range values

        # Smoothed values
        self.plus_di = None   # +DI value
        self.minus_di = None  # -DI value
        self.adx_value = None  # ADX value
        self.dx_values = []    # DX values for ADX calculation

    def _calculate_directional_movement(self, high: float, low: float) -> Tuple[float, float]:
        """
        Calculate +DM and -DM

        Args:
            high: Current period's high
            low: Current period's low

        Returns:
            Tuple[float, float]: (+DM, -DM) values
        """
        if self.prev_high is None or self.prev_low is None:
            self.prev_high = high
            self.prev_low = low
            return 0.0, 0.0

        up_move = high - self.prev_high
        down_move = self.prev_low - low

        self.prev_high = high
        self.prev_low = low

        if up_move > down_move and up_move > 0:
            plus_dm = up_move
        else:
            plus_dm = 0

        if down_move > up_move and down_move > 0:
            minus_dm = down_move
        else:
            minus_dm = 0

        return plus_dm, minus_dm

    def _calculate_true_range(self, high: float, low: float, prev_close: float) -> float:
        """
        Calculate True Range

        Args:
            high: Current period's high
            low: Current period's low
            prev_close: Previous period's close

        Returns:
            float: True Range value
        """
        return max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )

    def push(self, high: float, low: float, close: float) -> Tuple[float, float, float]:
        """
        Add new price data and calculate ADX

        Args:
            high: Current period's high price
            low: Current period's low price
            close: Current period's closing price

        Returns:
            Tuple[float, float, float]: (ADX, +DI, -DI) values if available, None otherwise
        """
        # Calculate +DM and -DM
        plus_dm, minus_dm = self._calculate_directional_movement(high, low)
        self.plus_dm.append(plus_dm)
        self.minus_dm.append(minus_dm)

        # Calculate True Range
        if len(self.plus_dm) > 1:  # We have a previous close
            tr = self._calculate_true_range(high, low, close)
            self.tr.append(tr)

        # Keep only needed periods
        if len(self.plus_dm) > self.period:
            self.plus_dm.pop(0)
            self.minus_dm.pop(0)
            self.tr.pop(0)

        # Calculate DI values when we have enough data
        if len(self.plus_dm) == self.period:
            # Smooth the directional movement values
            smoothed_plus_dm = sum(self.plus_dm)
            smoothed_minus_dm = sum(self.minus_dm)
            smoothed_tr = sum(self.tr)

            # Calculate +DI and -DI
            self.plus_di = (smoothed_plus_dm / smoothed_tr) * 100 if smoothed_tr > 0 else 0
            self.minus_di = (smoothed_minus_dm / smoothed_tr) * 100 if smoothed_tr > 0 else 0

            # Calculate DX
            di_diff = abs(self.plus_di - self.minus_di)
            di_sum = self.plus_di + self.minus_di
            dx = (di_diff / di_sum) * 100 if di_sum > 0 else 0

            self.dx_values.append(dx)

            # Keep only needed DX values
            if len(self.dx_values) > self.period:
                self.dx_values.pop(0)

            # Calculate ADX
            if len(self.dx_values) == self.period:
                self.adx_value = sum(self.dx_values) / self.period

        return self.adx_value, self.plus_di, self.minus_di

    def get_values(self) -> Tuple[float, float, float]:
        """
        Get current ADX, +DI, and -DI values

        Returns:
            Tuple[float, float, float]: (ADX, +DI, -DI) values if available, None otherwise
        """
        return self.adx_value, self.plus_di, self.minus_di