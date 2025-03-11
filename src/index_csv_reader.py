from datetime import datetime
import csv
from typing import Dict, List, Any

class IndexCSVReader:
    def __init__(self, file_path: str):
        """
        Initialize the IndexCSVReader with the CSV file path

        Args:
            file_path (str): Path to the CSV file containing index data
        """
        self.file_path = file_path
        self.data: Dict[datetime, Dict[str, float]] = {}

    def read_data(self) -> Dict[datetime, Dict[str, float]]:
        """
        Read and parse the CSV file into a dictionary

        Returns:
            Dict[datetime, Dict[str, float]]: Dictionary with dates as keys and
                                            daily data as nested dictionaries
        """
        try:
            with open(self.file_path, 'r') as file:
                csv_reader = csv.DictReader(file)

                for row in csv_reader:
                    # Parse date from DD-MMM-YYYY format
                    # Handle BOM character in CSV by cleaning the key
                    # Also clean up any leading/trailing whitespace in column names
                    row = {k.strip(): v for k, v in row.items()}
                    # print(row)
                    # print(row.keys())
                    if '\ufeffDate' in row:
                        date_str = row['\ufeffDate']
                    else:
                        date_str = row['Date']
                    date = datetime.strptime(date_str, '%d-%b-%Y')

                    # Create dictionary for this date's data
                    self.data[date] = {
                        'open': float(row['Open']) if row['Open'] else 0.0,
                        'high': float(row['High']) if row['High'] else 0.0,
                        'low': float(row['Low']) if row['Low'] else 0.0,
                        'close': float(row['Close']) if row['Close'] else 0.0,
                        'shares_traded': float(row['Shares Traded']) if row['Shares Traded'] else 0.0,
                        'turnover': float(row['Turnover']) if row['Turnover'] else 0.0
                    }

        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find file: {self.file_path}")
        except ValueError as e:
            raise ValueError(f"Error parsing data: {str(e)}")

        return self.data

    def get_data_as_lists(self) -> Dict[str, List[Any]]:
        """
        Convert the data into lists for each field

        Returns:
            Dict[str, List[Any]]: Dictionary with field names as keys and lists of values
        """
        if not self.data:
            self.read_data()

        result = {
            'dates': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'shares_traded': [],
            'turnover': []
        }

        # Sort dates to ensure chronological order
        sorted_dates = sorted(self.data.keys())

        for date in sorted_dates:
            result['dates'].append(date)
            daily_data = self.data[date]
            result['open'].append(daily_data['open'])
            result['high'].append(daily_data['high'])
            result['low'].append(daily_data['low'])
            result['close'].append(daily_data['close'])
            result['shares_traded'].append(daily_data['shares_traded'])
            result['turnover'].append(daily_data['turnover'])

        return result

"""
# Example usage:
if __name__ == "__main__":
    # Example usage of the class
    reader = IndexCSVReader("nifty_midcap_150.csv")
    data = reader.read_data()

    # Print first few entries
    for date in list(data.keys())[:5]:
        print(f"Date: {date.strftime('%d-%b-%Y')}")
        print(f"Data: {data[date]}")
        print("---")
"""
