import pandas as pd
from datetime import datetime, timedelta

df = pd.read_csv("temp_all_cities.csv")


last_date = datetime.strptime(df["Date"][0], '%m/%d/%Y')

for index, row in df.iterrows():
    current_date = datetime.strptime(row["Date"], '%m/%d/%Y')
    if (last_date != current_date):
        #print (current_date)
        if (not (last_date - timedelta(1) == current_date)):
            print ("MISSING DATE")
            print ("last_date")
            print ("new_date")
        else:
            last_date = current_date