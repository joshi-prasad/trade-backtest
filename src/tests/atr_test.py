import unittest
from atr import ATR

class TestATR(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.atr = ATR(period=3)  # Use small period for easier testing

    def test_initialization(self):
        """Test if ATR object is initialized correctly."""
        self.assertEqual(self.atr.period, 3)
        self.assertEqual(len(self.atr.true_ranges), 0)
        self.assertIsNone(self.atr.atr_value)
        self.assertIsNone(self.atr.prev_close)

    def test_first_tr_calculation(self):
        """Test True Range calculation for first period."""
        atr_value = self.atr.push(high=100.0, low=90.0, close=95.0)
        self.assertIsNone(atr_value)  # Not enough data for ATR yet
        self.assertEqual(self.atr.true_ranges[0], 10.0)  # High - Low = 100 - 90

    def test_subsequent_tr_calculation(self):
        """Test True Range calculation with previous close."""
        self.atr.push(high=100.0, low=90.0, close=95.0)
        self.atr.push(high=105.0, low=85.0, close=90.0)

        # TR should be max of:
        # 1. High - Low = 20
        # 2. |High - Prev Close| = |105 - 95| = 10
        # 3. |Low - Prev Close| = |85 - 95| = 10
        self.assertEqual(self.atr.true_ranges[1], 20.0)

    def test_atr_calculation(self):
        """Test ATR calculation over full period."""
        # Push 3 periods of data
        self.atr.push(high=100.0, low=90.0, close=95.0)   # TR = 10
        self.atr.push(high=105.0, low=85.0, close=90.0)   # TR = 20
        atr_value = self.atr.push(high=102.0, low=88.0, close=100.0)  # TR = 14

        # First ATR should be simple average: (10 + 20 + 14) / 3
        expected_atr = (10 + 20 + 14) / 3
        self.assertAlmostEqual(atr_value, expected_atr)

    def test_wilders_smoothing(self):
        """Test Wilder's smoothing for subsequent ATR values."""
        # Initial values
        self.atr.push(high=100.0, low=90.0, close=95.0)   # TR = 10
        self.atr.push(high=105.0, low=85.0, close=90.0)   # TR = 20
        first_atr = self.atr.push(high=102.0, low=88.0, close=100.0)  # TR = 14

        # Next value should use Wilder's smoothing
        next_atr = self.atr.push(high=104.0, low=96.0, close=98.0)  # TR = 8

        # Expected = ((Previous ATR * (period-1)) + Current TR) / period
        expected_atr = ((first_atr * 2) + 8) / 3
        self.assertAlmostEqual(next_atr, expected_atr)

    def test_get_atr(self):
        """Test getting ATR value."""
        self.assertIsNone(self.atr.get_atr())  # Should be None initially

        self.atr.push(high=100.0, low=90.0, close=95.0)
        self.atr.push(high=105.0, low=85.0, close=90.0)
        self.atr.push(high=102.0, low=88.0, close=100.0)

        self.assertIsNotNone(self.atr.get_atr())  # Should have value now

if __name__ == '__main__':
    unittest.main()