import unittest
from adx import ADX

class TestADX(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.adx = ADX(period=3)  # Use small period for easier testing

    def test_initialization(self):
        """Test if ADX object is initialized correctly."""
        self.assertEqual(self.adx.period, 3)
        self.assertIsNone(self.adx.prev_high)
        self.assertIsNone(self.adx.prev_low)
        self.assertEqual(len(self.adx.plus_dm), 0)
        self.assertEqual(len(self.adx.minus_dm), 0)
        self.assertEqual(len(self.adx.tr), 0)

    def test_first_directional_movement(self):
        """Test first directional movement calculation."""
        adx, plus_di, minus_di = self.adx.push(high=100.0, low=90.0, close=95.0)
        self.assertIsNone(adx)  # Not enough data
        self.assertIsNone(plus_di)
        self.assertIsNone(minus_di)
        self.assertEqual(self.adx.plus_dm[0], 0)  # First period has no DM
        self.assertEqual(self.adx.minus_dm[0], 0)

    def test_subsequent_directional_movement(self):
        """Test directional movement calculation with previous values."""
        self.adx.push(high=100.0, low=90.0, close=95.0)
        self.adx.push(high=105.0, low=92.0, close=98.0)  # Up move = 5, Down move = -2

        # Should record +DM since up move is larger
        self.assertEqual(self.adx.plus_dm[1], 5.0)
        self.assertEqual(self.adx.minus_dm[1], 0.0)

    def test_di_calculation(self):
        """Test Directional Indicator calculation."""
        # Push enough data for DI calculation
        self.adx.push(high=100.0, low=90.0, close=95.0)
        self.adx.push(high=105.0, low=92.0, close=98.0)
        _, plus_di, minus_di = self.adx.push(high=103.0, low=88.0, close=94.0)

        self.assertIsNotNone(plus_di)
        self.assertIsNotNone(minus_di)
        self.assertGreaterEqual(plus_di, 0)
        self.assertGreaterEqual(minus_di, 0)
        self.assertLessEqual(plus_di, 100)
        self.assertLessEqual(minus_di, 100)

    def test_adx_calculation(self):
        """Test ADX calculation over full period."""
        # Push enough data for ADX calculation
        self.adx.push(high=100.0, low=90.0, close=95.0)
        self.adx.push(high=105.0, low=92.0, close=98.0)
        self.adx.push(high=103.0, low=88.0, close=94.0)
        adx, _, _ = self.adx.push(high=107.0, low=93.0, close=105.0)

        self.assertIsNotNone(adx)
        self.assertGreaterEqual(adx, 0)
        self.assertLessEqual(adx, 100)

    def test_get_values(self):
        """Test getting ADX, +DI, and -DI values."""
        adx, plus_di, minus_di = self.adx.get_values()
        self.assertIsNone(adx)
        self.assertIsNone(plus_di)
        self.assertIsNone(minus_di)

        # Push enough data for calculations
        self.adx.push(high=100.0, low=90.0, close=95.0)
        self.adx.push(high=105.0, low=92.0, close=98.0)
        self.adx.push(high=103.0, low=88.0, close=94.0)

        adx, plus_di, minus_di = self.adx.get_values()
        self.assertIsNotNone(plus_di)
        self.assertIsNotNone(minus_di)

    def test_trend_strength(self):
        """Test ADX values for trend strength interpretation."""
        # Push data that should create a strong trend
        self.adx.push(high=100.0, low=90.0, close=95.0)
        self.adx.push(high=105.0, low=92.0, close=98.0)
        self.adx.push(high=110.0, low=95.0, close=108.0)
        adx, plus_di, minus_di = self.adx.push(high=115.0, low=98.0, close=112.0)

        if adx is not None:  # ADX is calculated
            # In a strong uptrend:
            # ADX should be high (> 25 indicates strong trend)
            # +DI should be greater than -DI
            self.assertGreater(plus_di, minus_di)

if __name__ == '__main__':
    unittest.main()