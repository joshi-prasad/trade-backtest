import unittest
from sma import SMA

class TestSMA(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.sma = SMA(3)  # Using 3 days for simpler test cases

    def test_initialization(self):
        """Test if SMA object is initialized correctly."""
        self.assertEqual(self.sma.days, 3)
        self.assertEqual(len(self.sma.prices), 0)
        self.assertEqual(self.sma.current_sum, 0.0)

    def test_insufficient_data(self):
        """Test behavior when insufficient data is available."""
        self.sma.push(10.0)
        self.assertIsNone(self.sma.get_sma())

        self.sma.push(11.0)
        self.assertIsNone(self.sma.get_sma())

    def test_sma_calculation(self):
        """Test if SMA is calculated correctly."""
        prices = [10.0, 11.0, 12.0]
        for price in prices:
            self.sma.push(price)

        expected_sma = sum(prices) / len(prices)
        self.assertAlmostEqual(self.sma.get_sma(), expected_sma)

    def test_moving_window(self):
        """Test if moving window works correctly."""
        # Push initial values
        initial_prices = [10.0, 11.0, 12.0]
        for price in initial_prices:
            self.sma.push(price)

        # Push a new value
        self.sma.push(13.0)  # Should remove 10.0
        expected_sma = (11.0 + 12.0 + 13.0) / 3
        self.assertAlmostEqual(self.sma.get_sma(), expected_sma)

    def test_multiple_updates(self):
        """Test multiple SMA updates."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        expected_values = [
            None,  # After first value
            None,  # After second value
            11.0,  # (10 + 11 + 12) / 3
            12.0,  # (11 + 12 + 13) / 3
            13.0,  # (12 + 13 + 14) / 3
        ]

        for price, expected in zip(prices, expected_values):
            self.sma.push(price)
            if expected is None:
                self.assertIsNone(self.sma.get_sma())
            else:
                self.assertAlmostEqual(self.sma.get_sma(), expected)

    def test_different_period(self):
        """Test SMA calculation with a different period."""
        sma5 = SMA(5)
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]

        for price in prices:
            sma5.push(price)

        expected_sma = sum(prices) / 5
        self.assertAlmostEqual(sma5.get_sma(), expected_sma)

if __name__ == '__main__':
    unittest.main()