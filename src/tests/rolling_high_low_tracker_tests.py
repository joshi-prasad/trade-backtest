import unittest
from rolling_high_low_tracker import RollingHighLowTracker

class TestRollingHighLowTracker(unittest.TestCase):

    def test_push_single_value(self):
        tracker = RollingHighLowTracker(5)
        low, high = tracker.push(100)
        self.assertEqual(low, 100)
        self.assertEqual(high, 100)

    def test_push_multiple_values(self):
        tracker = RollingHighLowTracker(5)
        tracker.push(100)
        tracker.push(105)
        tracker.push(98)
        low, high = tracker.push(102)
        self.assertEqual(low, 98)
        self.assertEqual(high, 105)

    def test_push_exceeding_lookback_period(self):
        tracker = RollingHighLowTracker(3)
        tracker.push(100)
        tracker.push(105)
        tracker.push(98)
        low, high = tracker.push(102)
        self.assertEqual(low, 98)
        self.assertEqual(high, 105)
        low, high = tracker.push(97)
        self.assertEqual(low, 97)
        self.assertEqual(high, 102)

    def test_push_with_decreasing_values(self):
        tracker = RollingHighLowTracker(3)
        tracker.push(105)
        tracker.push(100)
        tracker.push(95)
        low, high = tracker.push(90)
        self.assertEqual(low, 90)
        self.assertEqual(high, 100)

    def test_push_with_increasing_values(self):
        tracker = RollingHighLowTracker(3)
        tracker.push(90)
        tracker.push(95)
        tracker.push(100)
        low, high = tracker.push(105)
        self.assertEqual(low, 95)
        self.assertEqual(high, 105)

        def test_get_high_low_no_data(self):
            tracker = RollingHighLowTracker(5)
            low, high = tracker.get_high_low()
            self.assertIsNone(low)
            self.assertIsNone(high)

        def test_get_high_low_with_data(self):
            tracker = RollingHighLowTracker(5)
            tracker.push(100)
            tracker.push(105)
            tracker.push(98)
            low, high = tracker.get_high_low()
            self.assertEqual(low, 98)
            self.assertEqual(high, 105)

        def test_get_high_low_after_removal(self):
            tracker = RollingHighLowTracker(3)
            tracker.push(100)
            tracker.push(105)
            tracker.push(98)
            tracker.push(102)
            low, high = tracker.get_high_low()
            self.assertEqual(low, 98)
            self.assertEqual(high, 105)
            tracker.push(97)
            low, high = tracker.get_high_low()
            self.assertEqual(low, 97)
            self.assertEqual(high, 102)

if __name__ == '__main__':
    unittest.main()