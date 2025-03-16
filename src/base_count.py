import pandas as pd
from datetime import datetime
from rolling_high_low_tracker import RollingHighLowTracker

class BaseCounter:
    def __init__(self):
        self.monthly_high = RollingHighLowTracker(20)
        self.three_month_high = RollingHighLowTracker(63)

        self.base_count = 0
        self.base_high = 0
        self.in_base = False
        self.base_start_date: datetime = 0
        self.start_base_counting = False

    def get_base_count(self):
        return self.base_count

    def is_base_counting(self):
        return self.start_base_counting

    def reset_base(self):
        self.base_count = 0
        self.base_high = 0
        self.in_base = False
        self.base_start_date = 0
        self.start_base_counting = False

    def push(self,
        date: datetime,
        price: float,
        ema50: float,
        ema150: float,
        ema200: float):

        self.monthly_high.push(price)
        self.three_month_high.push(price)

        if price < ema200:
            # print(f"{date}: Price below 200EMA. Resetting base.")
            self.reset_base()
            return

        if self.start_base_counting == False:
            if price > ema150 and ema150 > ema200 and price > ema50:
                # print(f"{date}: Starting base counting")
                self.start_base_counting = True
                self.in_base = True
                self.base_start_date = date
                self.base_count = 0
                (_, self.base_high) = self.monthly_high.get_high_low()
            return

        if self.in_base == False:
            if price < ema50:
                # print(f"{date}: Price below 50MA. Forming base.")
                self.in_base = True
                self.base_start_date = date
                (_, self.base_high) = self.monthly_high.get_high_low()
            return

        if (price > self.base_high) and (price > ema50) and (date - self.base_start_date).days < 20:
            # print(f"{date}: Price above base high. No longer in base.")
            # self.in_base = False
            return

        gain = (price - self.base_high) / self.base_high
        if price > self.base_high and gain > 0.1:
            # print(f"{date}: Price above base high. with gain {gain}. BaseCount={self.base_count+1}.")
            self.base_count += 1
            self.in_base = False
            return

        # if ((date - self.base_start_date).days) > 60:
        #     self.base_start_date += pd.Timedelta(weeks=4)
        #     (_, self.base_high) = self.three_month_high.get_high_low()

# Example usage
if __name__ == "__main__":
    # Load your data into a DataFrame
    data = pd.read_csv(
        "../indices_data/nifty_midcap_50.csv", parse_dates=['Date'], index_col='Date', dayfirst=True)

    # Trim spaces in column names
    data.columns = data.columns.str.strip()

    data['200EMA'] = data['Close'].ewm(span=200, adjust=False).mean()
    data['150EMA'] = data['Close'].ewm(span=150, adjust=False).mean()
    data['50MA'] = data['Close'].rolling(window=50).mean()

    base_counter = BaseCounter()

    for i in range(len(data)):
        current_price = data['Close'].iloc[i]
        current_date = data.index[i]
        ema50 = data['50MA'].iloc[i]
        ema150 = data['150EMA'].iloc[i]
        ema200 = data['200EMA'].iloc[i]
        base_counter.push(
            date=current_date.to_pydatetime(),
            price=current_price,
            ema50=ema50,
            ema150=ema150,
            ema200=ema200
        )