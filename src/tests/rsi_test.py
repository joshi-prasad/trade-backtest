import unittest
from rsi import RSI

class TestRSI(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.rsi = RSI(period=3)  # Use small period for easier testing

    def test_initialization(self):
        """Test if RSI object is initialized correctly."""
        self.assertEqual(self.rsi.period, 3)
        self.assertIsNone(self.rsi.prev_close)
        self.assertEqual(len(self.rsi.gains), 0)
        self.assertEqual(len(self.rsi.losses), 0)
        self.assertIsNone(self.rsi.avg_gain)
        self.assertIsNone(self.rsi.avg_loss)
        self.assertIsNone(self.rsi.rsi_value)

    def test_first_change_calculation(self):
        """Test price change calculation for first value."""
        rsi_value = self.rsi.push(close=100.0)
        self.assertIsNone(rsi_value)  # Not enough data for RSI yet
        self.assertEqual(self.rsi.gains[0], 0.0)
        self.assertEqual(self.rsi.losses[0], 0.0)

    def test_gain_calculation(self):
        """Test gain calculation for price increase."""
        self.rsi.push(close=100.0)
        self.rsi.push(close=110.0)  # 10 point gain
        self.assertEqual(self.rsi.gains[1], 10.0)
        self.assertEqual(self.rsi.losses[1], 0.0)

    def test_loss_calculation(self):
        """Test loss calculation for price decrease."""
        self.rsi.push(close=100.0)
        self.rsi.push(close=90.0)  # 10 point loss
        self.assertEqual(self.rsi.gains[1], 0.0)
        self.assertEqual(self.rsi.losses[1], 10.0)

    def test_rsi_calculation(self):
        """Test RSI calculation over full period."""
        # Push 3 periods of data with clear trend
        self.rsi.push(close=100.0)
        self.rsi.push(close=110.0)  # +10
        rsi_value = self.rsi.push(close=120.0)  # +10

        # All gains, no losses should give RSI = 100
        self.assertIsNotNone(rsi_value)
        self.assertEqual(rsi_value, 100.0)

    def test_smoothed_calculation(self):
        """Test smoothed average calculation after initial period."""
        # Initial period
        self.rsi.push(close=100.0)
        self.rsi.push(close=110.0)  # +10
        self.rsi.push(close=120.0)  # +10

        # Next value
        rsi_value = self.rsi.push(close=115.0)  # -5

        # Should use smoothed averages
        self.assertIsNotNone(rsi_value)
        self.assertLess(rsi_value, 100.0)  # RSI should decrease due to loss

    def test_overbought_condition(self):
        """Test overbought condition detection."""
        # Create strong upward trend
        self.rsi.push(close=100.0)
        self.rsi.push(close=110.0)
        self.rsi.push(close=120.0)

        self.assertTrue(self.rsi.is_overbought())
        self.assertFalse(self.rsi.is_oversold())

    def test_oversold_condition(self):
        """Test oversold condition detection."""
        # Create strong downward trend
        self.rsi.push(close=100.0)
        self.rsi.push(close=90.0)
        self.rsi.push(close=80.0)

        self.assertTrue(self.rsi.is_oversold())
        self.assertFalse(self.rsi.is_overbought())

    def test_custom_thresholds(self):
        """Test custom thresholds for overbought/oversold."""
        self.rsi.push(close=100.0)
        self.rsi.push(close=110.0)
        self.rsi.push(close=120.0)

        # Test with custom thresholds
        self.assertTrue(self.rsi.is_overbought(threshold=80.0))
        self.assertFalse(self.rsi.is_oversold(threshold=20.0))

    def test_get_rsi(self):
        """Test getting RSI value."""
        self.assertIsNone(self.rsi.get_rsi())  # Should be None initially

        self.rsi.push(close=100.0)
        self.rsi.push(close=110.0)
        self.rsi.push(close=120.0)

        self.assertIsNotNone(self.rsi.get_rsi())  # Should have value now

    def test_neutral_rsi(self):
        """Test RSI calculation with mixed gains and losses."""
        self.rsi.push(close=100.0)
        self.rsi.push(close=110.0)  # +10
        self.rsi.push(close=100.0)  # -10

        rsi_value = self.rsi.get_rsi()
        self.assertIsNotNone(rsi_value)
        self.assertGreater(rsi_value, 0)
        self.assertLess(rsi_value, 100)

    def test_rsi_19_period(self):
        """Test RSI calculation with 19-period interval."""
        # Create RSI with 19-period interval
        rsi_19 = RSI(period=19)

        # Push 19 values with alternating increases/decreases
        values = [100.0, 102.0, 101.0, 103.0, 102.0, 104.0, 103.0, 105.0, 104.0,
                 106.0, 105.0, 107.0, 106.0, 108.0, 107.0, 109.0, 108.0, 110.0, 109.0]

        for value in values:
            rsi_19.push(close=value)

        # Get final RSI value
        rsi_value = rsi_19.get_rsi()

        # Verify RSI value is calculated and within valid range
        self.assertIsNotNone(rsi_value)
        self.assertGreater(rsi_value, 0)
        self.assertLess(rsi_value, 100)

        # With alternating gains/losses, RSI should be close to 50
        self.assertGreater(rsi_value, 45)
        self.assertLess(rsi_value, 55)


if __name__ == '__main__':
    unittest.main()