import unittest
from datetime import datetime
import os
from index_csv_reader import IndexCSVReader

class TestIndexCSVReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        cls.test_file = "./src/tests/test_data/sample_index.csv"
        cls.reader = IndexCSVReader(cls.test_file)

    def test_file_initialization(self):
        """Test if the IndexCSVReader is initialized correctly."""
        reader = IndexCSVReader(self.test_file)
        self.assertEqual(reader.file_path, self.test_file)
        self.assertEqual(len(reader.data), 0)

    def test_read_data(self):
        """Test if data is read correctly from CSV."""
        data = self.reader.read_data()

        # Check if we have the correct number of entries
        self.assertEqual(len(data), 5)

        # Check first entry
        first_date = datetime(2019, 1, 14)
        first_entry = data[first_date]
        self.assertAlmostEqual(first_entry['open'], 4500.25)
        self.assertAlmostEqual(first_entry['high'], 4550.75)
        self.assertAlmostEqual(first_entry['low'], 4480.50)
        self.assertAlmostEqual(first_entry['close'], 4525.60)
        self.assertAlmostEqual(first_entry['shares_traded'], 1000000)
        self.assertAlmostEqual(first_entry['turnover'], 450.50)

    def test_get_data_as_lists(self):
        """Test if data is correctly converted to lists format."""
        list_data = self.reader.get_data_as_lists()

        # Check if all expected keys exist
        expected_keys = ['dates', 'open', 'high', 'low', 'close', 'shares_traded', 'turnover']
        self.assertEqual(set(list_data.keys()), set(expected_keys))

        # Check if all lists have the same length
        list_lengths = [len(list_data[key]) for key in expected_keys]
        self.assertEqual(len(set(list_lengths)), 1)  # All lengths should be the same
        self.assertEqual(list_lengths[0], 5)  # Should have 5 entries

        # Check if dates are in chronological order
        dates = list_data['dates']
        self.assertEqual(len(dates), 5)
        self.assertTrue(all(dates[i] <= dates[i+1] for i in range(len(dates)-1)))

    def test_nonexistent_file(self):
        """Test handling of non-existent file."""
        reader = IndexCSVReader("nonexistent.csv")
        with self.assertRaises(FileNotFoundError):
            reader.read_data()

    def test_data_consistency(self):
        """Test if data remains consistent between reads."""
        # Read data twice
        data1 = self.reader.read_data()
        data2 = self.reader.read_data()

        # Check if both reads return the same data
        self.assertEqual(len(data1), len(data2))
        for date in data1:
            self.assertEqual(data1[date], data2[date])

    def test_data_types(self):
        """Test if data types are correct for all fields."""
        data = self.reader.read_data()
        first_date = min(data.keys())
        entry = data[first_date]

        # Check types
        self.assertIsInstance(first_date, datetime)
        self.assertIsInstance(entry['open'], float)
        self.assertIsInstance(entry['high'], float)
        self.assertIsInstance(entry['low'], float)
        self.assertIsInstance(entry['close'], float)
        self.assertIsInstance(entry['shares_traded'], float)
        self.assertIsInstance(entry['turnover'], float)

    def test_sorted_dates_in_lists(self):
        """Test if dates are properly sorted in list format."""
        list_data = self.reader.get_data_as_lists()
        dates = list_data['dates']

        # Check if dates are sorted
        sorted_dates = sorted(dates)
        self.assertEqual(dates, sorted_dates)

        # Verify corresponding data alignment
        first_date_index = dates.index(min(dates))
        data = self.reader.read_data()
        self.assertAlmostEqual(
            list_data['close'][first_date_index],
            data[min(dates)]['close']
        )

if __name__ == '__main__':
    unittest.main()