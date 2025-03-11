class EMA:
    def __init__(self, days):
        """
        Initialize EMA calculator

        Args:
            days (int): Number of days for EMA calculation
        """
        self.days = days
        self.multiplier = 2 / (days + 1)
        self.prices = []
        self.current_ema = None

    def push(self, price):
        """
        Add a new price data point

        Args:
            price (float): The closing price for the day
        """
        self.prices.append(price)

        # If we don't have enough data for initial SMA, just store the price
        if len(self.prices) < self.days:
            return

        # Calculate initial SMA when we have exactly enough prices
        if len(self.prices) == self.days:
            self.current_ema = sum(self.prices) / self.days
            return

        # Calculate EMA for subsequent prices
        self.current_ema = \
            (price - self.current_ema) * self.multiplier + self.current_ema
        return self.current_ema

    def get_ema(self):
        """
        Get the current EMA value

        Returns:
            float: Current EMA value if available, None otherwise
        """
        return self.current_ema
