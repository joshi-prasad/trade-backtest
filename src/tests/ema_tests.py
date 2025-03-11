import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ema import EMA

class TestEMA(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.ema = EMA(3)  # Using 3 days for simpler test cases

    def test_initialization(self):
        """Test if EMA object is initialized correctly."""
        self.assertEqual(self.ema.days, 3)
        self.assertAlmostEqual(self.ema.multiplier, 0.5)  # 2/(3+1)
        self.assertEqual(len(self.ema.prices), 0)
        self.assertIsNone(self.ema.current_ema)

    def test_insufficient_data(self):
        """Test behavior when insufficient data is available."""
        self.ema.push(10.0)
        self.assertIsNone(self.ema.get_ema())

        self.ema.push(11.0)
        self.assertIsNone(self.ema.get_ema())

    def test_initial_sma_calculation(self):
        """Test if initial SMA is calculated correctly."""
        prices = [10.0, 11.0, 12.0]
        for price in prices:
            self.ema.push(price)

        # Initial EMA should be SMA of first 3 values
        expected_sma = sum(prices) / len(prices)
        self.assertAlmostEqual(self.ema.get_ema(), expected_sma)

    def test_ema_calculation(self):
        """Test if EMA is calculated correctly after initial period."""
        # First 3 values for initial SMA
        prices = [10.0, 11.0, 12.0]
        for price in prices:
            self.ema.push(price)

        # Add a new value and verify EMA calculation
        new_price = 13.0
        self.ema.push(new_price)

        # Previous EMA was 11.0 (SMA of first 3 values)
        # Multiplier is 0.5
        # New EMA = (13.0 - 11.0) * 0.5 + 11.0 = 12.0
        self.assertAlmostEqual(self.ema.get_ema(), 12.0)

    def test_multiple_ema_updates(self):
        """Test multiple EMA updates after initial period."""
        # Initial values
        initial_prices = [10.0, 11.0, 12.0]
        for price in initial_prices:
            self.ema.push(price)

        # Add more values and verify EMA updates
        self.ema.push(13.0)  # EMA should be 12.0
        self.assertAlmostEqual(self.ema.get_ema(), 12.0)

        self.ema.push(14.0)  # EMA should be 13.0
        self.assertAlmostEqual(self.ema.get_ema(), 13.0)

    def test_different_period(self):
        """Test EMA calculation with a different period."""
        ema5 = EMA(5)
        self.assertAlmostEqual(ema5.multiplier, 2/6)  # 2/(5+1)

    def test_ema9(self):
        """ Test EMA with 9 day period. """
        ema9 = EMA(9)
        initial_prices = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        for price in initial_prices:
            ema9.push(price)
        self.assertEqual(ema9.get_ema(), 10)

if __name__ == '__main__':
    unittest.main()