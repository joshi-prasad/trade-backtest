from collections import deque

class SMA:
    def __init__(self, days):
        """
        Initialize SMA calculator

        Args:
            days (int): Number of days for SMA calculation
        """
        self.days = days
        self.prices = deque(maxlen=days)
        self.current_sum = 0.0

    def push(self, price):
        """
        Add a new price data point

        Args:
            price (float): The closing price for the day
        """
        if len(self.prices) == self.days:
            self.current_sum -= self.prices[0]

        self.prices.append(price)
        self.current_sum += price

    def get_sma(self):
        """
        Get the current SMA value

        Returns:
            float: Current SMA value if available, None otherwise
        """
        if len(self.prices) < self.days:
            return None
        return self.current_sum / self.days