import os

# get list of all csv files in the current directory
def get_csv_files():
    files = os.listdir()
    csv_files = []
    for file in files:
        if file.endswith('.csv'):
            csv_files.append(file)
    return csv_files

def get_weeks(csv_file):
    # returns weeks from csv file.
    weeks = []
    with open(csv_file, 'r') as f:
        for line in f:
            week = line.split(',')[0]
            weeks.append(week)
    return weeks

def populate_missing_week(csv_file, previous_week, current_week):
    # read the csv file and add the missing week
    tmp_file = 'tmp.csv'
    with open(csv_file, 'r') as f, open(tmp_file, 'w') as t:
        for line in f:
            if line.startswith(current_week):
                # the csv file has two values for the current week
                # in the format 'date,close'
                # get the value of close for the current week
                # and add the missing week
                close = line.split(',')[1]
                t.write(previous_week + " 15:30:00"+ ',' + close)
            t.write(line)
    os.remove(csv_file)
    os.rename(tmp_file, csv_file)
    print("Updated", csv_file)

previous_week = "16/10/2015"
current_week = "23/10/2015"

previous_week = "01/03/2024"
current_week = "07/03/2024"

for csv_file in get_csv_files():
    weeks = get_weeks(csv_file)
    if previous_week not in weeks:
        populate_missing_week(csv_file, previous_week, current_week)