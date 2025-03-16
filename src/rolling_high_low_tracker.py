"""
RollingHighLowTracker

This class maintains the highest and lowest values of a given price series over a specified lookback period.
It is useful for tracking metrics such as the 52-week high and low, 1-month high and low, 3-month high and low, etc.

Usage:
- Instantiate the class with a lookback period (e.g., 20 for 1-month high/low, 63 for 3-month high/low, 252 for 52-week high/low).
- Use the `push(price: float) -> tuple[float, float]` method to update the rolling high and low with a new closing price.
- Use the `get_high_low() -> tuple[float, float]` method to fetch the current high and low values for the period.

Methods:
- `push(price: float)`: Adds a new closing price to the rolling window and updates the high/low values.
- `get_high_low()`: Returns the current (low, high) values for the given lookback period.

Example:
    tracker = RollingHighLowTracker(20)  # 1-month high/low tracker
    tracker.push(100)
    tracker.push(105)
    tracker.push(98)
    print(tracker.get_high_low())  # (98, 105)

Author: Your Name
"""
from collections import deque

class RollingHighLowTracker:
    def __init__(self, lookback_period: int):
        """
        Initializes the tracker with a specified lookback period.

        :param lookback_period: Number of days to track for high and low values.
        """
        self.lookback_period = lookback_period
        self.prices = deque(maxlen=lookback_period)

    def push(self, price: float) -> tuple[float, float]:
        """
        Adds a new closing price and updates the rolling high and low.

        :param price: Today's closing price.
        :return: Tuple containing (low value, high value) for the given period.
        """
        self.prices.append(price)
        return self.get_high_low()

    def get_high_low(self) -> tuple[float, float]:
        """
        Fetches the current high and low values for the period.

        :return: Tuple (low value, high value)
        """
        if not self.prices:
            return (None, None)  # No data available yet
        return (min(self.prices), max(self.prices))

# Example usage
if __name__ == "__main__":
    tracker = RollingHighLowTracker(20)  # 1-month high/low tracker
    prices = [100, 105, 98, 110, 95, 102, 108]

    for price in prices:
        print(f"New Price: {price}, High/Low: {tracker.push(price)}")
