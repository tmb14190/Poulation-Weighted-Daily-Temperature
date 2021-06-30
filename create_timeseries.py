'''
Created on 30 Jun 2021

@author: jackm
'''
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


df = pd.read_csv("temp_all_cities_added_lat_lon.csv")

timeseries_df = pd.DataFrame(columns=["Date", "Mean Temp C", "Mean Min Temp C", "Mean Max Temp C", "Abs Min Temp C", "Abs Max Temp C"])

last_date = datetime.strptime(df["Date"][0], '%m/%d/%Y')

cities_recorded_today = 0
washington = []
missing_day_flag = False
previous_day_temp = [0, 0, 0, 0, 0]
means = [0, 0, 0]
_min = 0
_max = 0

for index, row in df.iterrows():
    current_date = datetime.strptime(row["Date"], '%m/%d/%Y')
        
    if (last_date != current_date):
        
        # If we have a missing day we want to hold the previous days temp, wait to calculate the next days temp, then average out these two days
        # A day of missing temperatures counts as a day with <3 recorded temperatures, these happen on
        # 3/14/2021, 11/1/2020, 3/8/2020, 11/3/2019, 3/10/2019, 11/4/2018, 3/11/2018
        # 11/5/2017, 9/16/2017, 3/12/2017, 11/6/2016, 3/13/2016, 11/1/2015, 3/8/2015
        # Where only Phoenix offers a temperature, which is too little information to base a days temperature on, and so we use previous and next days instead
        # If we have two missing days ina  row this breaks, but after checking the data with missing_days_check.py this is not the case
        if (missing_day_flag):
            timeseries_df = timeseries_df.append( [{"Date":last_date-timedelta(1), "Mean Temp C":(means[0] + previous_day_temp[0]) /2, "Mean Min Temp C":(means[1] + previous_day_temp[1]) /2, 
                                   "Mean Max Temp C":(means[2] + previous_day_temp[2]) /2, "Abs Min Temp C":min(_min, previous_day_temp[3]), "Abs Max Temp C":max(_max, previous_day_temp[4]), "Projected":True}] )
            missing_day_flag = False
        if (cities_recorded_today < 3):
            missing_day_flag = True
            cities_recorded_today = 0
            last_date = current_date
            continue
        
        #print (washington)
        arrays = [np.array(x) for x in washington]
        washington_temp_average = [np.mean(k) for k in zip(*arrays)]
        #print (washington_temp_average)
        means[0] += washington_temp_average[0]
        means[1] += washington_temp_average[1]
        means[2] += washington_temp_average[2]
        
        timeseries_df = timeseries_df.append( [{"Date":last_date, "Mean Temp C":means[0], "Mean Min Temp C":means[1], "Mean Max Temp C":means[2], "Abs Min Temp C":_min, "Abs Max Temp C":_max, "Projected":False}] )
        
        # just holding the previous days average in case we need it for a missing day
        previous_day_temp[0] = means[0]
        previous_day_temp[1] = means[1]
        previous_day_temp[2] = means[2]
        previous_day_temp[3] = _min
        previous_day_temp[4] = _max
        means = [0, 0, 0]
        _min = 0
        _max = 0
        last_date = current_date
        cities_recorded_today = 0
        continue

    weight = row["Weighted Pop"]
    cities_recorded_today += 1
    if (row["City/State"] == "Washington/District of Columbia"):
        washington.append([row["Mean"] * weight, row["Min"] * weight, row["Max"] * weight])
    
    means[0] += row["Mean"] * weight
    means[1] += row["Min"] * weight
    means[2] += row["Max"] * weight
    
    if (row["Min"] < _min): _min = row["Min"]
    if (row["Max"] > _max): _max = row["Max"]

timeseries_df.to_csv("timeseries_added_lat_lon.csv", index=False)
    
    
    
    