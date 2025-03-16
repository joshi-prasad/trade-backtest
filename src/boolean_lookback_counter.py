from collections import deque
"""
A class to count the number of True and False values within a specified
lookback period.

Attributes:
    lookback_period (int): The number of most recent boolean values to
    consider.

    values (deque): A deque to store the boolean values with a maximum length
    of lookback_period.

Methods:
    push(value: bool):
        Adds a new boolean value to the deque.

    count_true() -> int:
        Returns the count of True values in the deque.

    count_false() -> int:
        Returns the count of False values in the deque.
"""

class BooleanLookbackCounter:
    def __init__(self, lookback_period: int):
        self.lookback_period = lookback_period
        self.values = deque(maxlen=lookback_period)

    def get_lookback_period(self) -> int:
        return self.lookback_period

    def push(self, value: bool):
        self.values.append(value)

    def count_true(self) -> int:
        return sum(self.values)

    def count_false(self) -> int:
        return len(self.values) - self.count_true()