'''
Created on 29 Jun 2021

@author: jackm

In this we associate Albany and Portland Maine with the closest cities to them, which are Springfield Massachusetts, and 
Manchester New Hampshire respectively. Arguably Albany could instead be associated with Syracuse New York instead of Springfield,
as Springfield could be identified in coalition with Hartford to the Windsor Locks temperature reading. But the methodology is to 
as basically as possible, link each sensor to their nearest city. Raleigh and Durham are the exception where both are connected to 
a single sensor, as the alternative is counterintuitive.
'''
import pandas as pd
from math import cos, asin, sqrt, pi

# Calculate distances to find closest sensor points for cities
def calculate_distance(lat1, lon1, lat2, lon2):
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return int(12742 * asin(sqrt(a))) #2*R*asin...

# Add the temperature readings to closest city
def add_known_temp_row(temp_readings, temp_row, pop_row, total_pop):
    #print (pop_row)
    weighted_pop = pop_row["population"].values[0] / total_pop
    city_state = pop_row["City"].values[0] + "/" + pop_row["State"].values[0]
    temp_readings.append({ "Date":temp_row["location_date"], "City/State":city_state, 
                      "Weighted Pop":weighted_pop, "Lon":pop_row["Lon"].values[0], "Lat":pop_row["Lat"].values[0], "Mean":temp_row["temp_mean_c"],  
                      "Min":temp_row["temp_min_c"], "Max":temp_row["temp_max_c"]})
    return temp_readings

# Calculate the 3 closest sensor points, and based on their distance weighting average a temperature reading for the city
def add_estimated_temp_row(temp_estimates, temp_readings, date, pop_row, total_pop):
    
    # Just used to weight the min 3 distances, with closest being heaviest weight, normalised to a combined weighting of 1 
    def weight_distances(sorted_keys):
        total_distance = sum(sorted_keys)
        weights = []
        for i in range(0, 3): weights.append((total_distance / sorted_keys[i]) / total_distance)
        normaliser = 1 / (sum(weights))
        return [weight * normaliser for weight in weights]
    
    weighted_pop = pop_row["population"] / total_pop
     
    lon = pop_row["Lon"]
    lat = pop_row["Lat"]
    distances = {}
    for reading in temp_readings:
        distance = calculate_distance(lat, lon, reading["Lat"], reading["Lon"])
        distances[distance] = reading["City/State"]
        
    sorted_distances = sorted(list(distances.keys()))[:3] # get 3 closest cities
    
    # If there are less than 3 cities then temperature readings are inaccurate and this days temperature will be calculated
    # by averaging the day before and day after 
    if (len(sorted_distances) < 3):
        return []
    
    weights = weight_distances(sorted_distances)
    means = [0, 0, 0]
    mins = [0, 0, 0]
    maxs = [0, 0, 0]
    
    # this is ugly and surely can be simplified but it does work
    for reading in temp_readings:
        for key in distances:
            if (key in sorted_distances):
                if (distances[key] == reading["City/State"]):
                    means[sorted_distances.index(key)] = reading["Mean"]
                    mins[sorted_distances.index(key)] = reading["Min"]
                    maxs[sorted_distances.index(key)] = reading["Max"]
    
    mean = means[0]*weights[0] + means[1]*weights[1] + means[2]*weights[2]
    _min = mins[0]*weights[0] + mins[1]*weights[1] + mins[2]*weights[2]
    _max = maxs[0]*weights[0] + maxs[1]*weights[1] + maxs[2]*weights[2]
         
    city_state = pop_row["City"] + "/" + pop_row["State"]
    
    temp_estimates.append({"Date":date, "City/State":city_state, "Weighted Pop":weighted_pop, "Lon":pop_row["Lon"], "Lat":pop_row["Lat"], "Mean":mean, "Min":_min, "Max":_max})
    return temp_estimates
    

pop_df = pd.read_csv("Population Data.csv")
temp_df = pd.read_csv("Temperature Data.csv")

# Our new dataframe for read and estimated temperatures for each city with weighted population
new_df = pd.DataFrame(columns=["Date", "City/State", "Weighted Pop", "Lon", "Lat", "Mean", "Min", "Max"])

total_pop = pop_df["population"].sum()

# Closest cities / airports relating to cities
closest_city = {"Covington":"Cincinnati", "Chicago O'Hare":"Chicago", "Phoenix/Sky HRBR":"Phoenix", "Wash DC/Dulles":"Washington", "Detroit/Wayne":"Detroit",
                 "Sacramento/Execu":"Sacramento", "St Louis/Lambert":"St. Louis", "NYC/LaGuardia":"New York", "Windsor Locks":"Hartford"}


last_date = temp_df["location_date"][0]
stations = temp_df["name"].unique()

temp_readings = []
temp_estimates = []

# In here we iterate through temperature data and link the stations to closest cities,
# then when the date changes to a new day, we estimate the temperature for all other cities
# in the population data.
for index, temp_row in temp_df.iterrows():
    
    if (last_date != temp_row["location_date"]): # when its a new day we need to estimate the cities without temperature readings
        
        for index, pop_row in pop_df.iterrows(): # go through all the cities in population data to estimate their temp readings
            
            # If reading already taken skip estimation
            reading_already_done = False
            for row in temp_readings:
                city_state = pop_row["City"] + "/" + pop_row["State"]
                if (row["City/State"] == city_state):
                    reading_already_done = True
            if (reading_already_done): continue
            
            temp_estimates = add_estimated_temp_row(temp_estimates, temp_readings, last_date, pop_row, total_pop)
        
        # add our new readings for the day to the dataframe being created and reset variables for next day
        new_df = new_df.append(temp_readings)
        new_df = new_df.append(temp_estimates)
        temp_readings = []
        temp_estimates = []
        last_date = temp_row["location_date"]
    
    name = temp_row["name"]
    pop_row = None
    
    # link our sensors to their closest cities
    if (name == "Raleigh/Durham"):
        pop_row = pop_df[(pop_df["City"] == "Raleigh")]
    
    if (name == "Richmond"): # two richmonds, need to specifiy this is the Virginia one
        pop_row = pop_df[(pop_df["City"] == "Richmond") & (pop_df["State"] == "Virginia")]
    
    if (name == "Albany"):
        pop_row = pop_df[(pop_df["City"] == "Springfield") & (pop_df["State"] == "Massachusetts")]
    
    if (name == "Portland"):
        if (temp_row["station_code"] == "KPDX"):
            pop_row = pop_df[(pop_df["City"] == "Portland")]
        else:
            pop_row = pop_df[(pop_df["City"] == "Manchester")]
    
    if (name in closest_city and pop_row is None):
        pop_row = pop_df[pop_df["City"].str.match(closest_city[name])]
    elif(pop_row is None):
        pop_row = pop_df[pop_df["City"].str.match(name)] # These are cities which have perfect matches in the pop data
    
    if (pop_row is None):
        raise Exception("Unknown City")
    
    temp_readings = add_known_temp_row(temp_readings, temp_row, pop_row, total_pop)
    
    if (name == "Raleigh/Durham"): # add the additional entry for raleigh/durham
        pop_row = pop_df[(pop_df["City"] == "Durham")]
        temp_readings = add_known_temp_row(temp_readings, temp_row, pop_row, total_pop)
        

new_df.to_csv("temp_all_cities.csv", index=False)

df = new_df

from datetime import datetime, timedelta
import numpy as np

timeseries_df = pd.DataFrame(columns=["Date", "Mean Temp C", "Mean Min Temp C", "Mean Max Temp C", "Abs Min Temp C", "Abs Max Temp C"])

last_date = datetime.strptime(df["Date"][0], '%m/%d/%Y')

cities_recorded_today = 0
washington = []
missing_day_flag = False
previous_day_temp = [0, 0, 0, 0, 0]
means = [0, 0, 0]
_min = 0
_max = 0

# Here we average all the cities weighted temeperature to create the daily timeseries for the entire US 
for index, row in df.iterrows():
    current_date = datetime.strptime(row["Date"], '%m/%d/%Y')
       
    # if theres a new date then lets add the new daily temperature for the entire US to our timeseries
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
        
        arrays = [np.array(x) for x in washington]
        washington_temp_average = [np.mean(k) for k in zip(*arrays)]
        means[0] += washington_temp_average[0]
        means[1] += washington_temp_average[1]
        means[2] += washington_temp_average[2]
        
        timeseries_df = timeseries_df.append( [{"Date":last_date, "Mean Temp C":means[0], "Mean Min Temp C":means[1], "Mean Max Temp C":means[2], "Abs Min Temp C":_min, "Abs Max Temp C":_max, "Projected":False}] )
        
        # just holding the previous days average for when we need it for a missing day
        # resetting our variables for a new day
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
    
    # sum the weighted averages for the day
    weight = row["Weighted Pop"]
    cities_recorded_today += 1
    if (row["City/State"] == "Washington/District of Columbia"): # we now deal with the washington problem where there are two entries
        washington.append([row["Mean"] * weight, row["Min"] * weight, row["Max"] * weight])
    
    means[0] += row["Mean"] * weight
    means[1] += row["Min"] * weight
    means[2] += row["Max"] * weight
    
    if (row["Min"] < _min): _min = row["Min"]
    if (row["Max"] > _max): _max = row["Max"]

timeseries_df.to_csv("timeseries_added_lat_lon.csv", index=False)
