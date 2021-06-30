'''
Created on 29 Jun 2021

@author: jackm

In this one we are dropping Albany and Portland Maine as an assumption could be that these are unusable data points
as they cannot be associated with any nearby city 
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

def add_unknown_temp_row(temp_estimates, temp_readings, date, pop_row, total_pop):
    
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
        
    sorted_distances = sorted(list(distances.keys()))[:3]
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
    min = mins[0]*weights[0] + mins[1]*weights[1] + mins[2]*weights[2]
    max = maxs[0]*weights[0] + maxs[1]*weights[1] + maxs[2]*weights[2]
         
    city_state = pop_row["City"] + "/" + pop_row["State"]
    
    temp_estimates.append({"Date":date, "City/State":city_state, "Weighted Pop":weighted_pop, "Lon":pop_row["Lon"], "Lat":pop_row["Lat"], "Mean":mean, "Min":min, "Max":max})
    return temp_estimates
    

pop_df = pd.read_csv("Population Data.csv")
temp_df = pd.read_csv("Temperature Data.csv")

new_df = pd.DataFrame(columns=["Date", "City/State", "Weighted Pop", "Lon", "Lat", "Mean", "Min", "Max"])

print (temp_df["name"].unique())

#print (pop_df[(pop_df["City"] == "Richmond") & (pop_df["State"] == "Virginia")])

total_pop = pop_df["population"].sum()
closest_city = {"Covington":"Cincinnati", "Chicago O'Hare":"Chicago", "Phoenix/Sky HRBR":"Phoenix", "Wash DC/Dulles":"Washington", "Detroit/Wayne":"Detroit",
                 "Sacramento/Execu":"Sacramento", "St Louis/Lambert":"St. Louis", "NYC/LaGuardia":"New York", "Windsor Locks":"Hartford"}


last_date = temp_df["location_date"][0]
stations = temp_df["name"].unique()

temp_readings = []
temp_estimates = []

for index, temp_row in temp_df.iterrows():
    
    if (last_date != temp_row["location_date"]):
        
        for index, pop_row in pop_df.iterrows():
            
            # If reading already taken skip estimation
            reading_already_done = False
            for row in temp_readings:
                city_state = pop_row["City"] + "/" + pop_row["State"]
                if (row["City/State"] == city_state):
                    reading_already_done = True
            if (reading_already_done): continue
            
            temp_estimates = add_unknown_temp_row(temp_estimates, temp_readings, last_date, pop_row, total_pop)
        
        new_df = new_df.append(temp_readings)
        new_df = new_df.append(temp_estimates)
        temp_readings = []
        temp_estimates = []
        last_date = temp_row["location_date"]
    
    name = temp_row["name"]
    pop_row = None
    
    if (name == "Raleigh/Durham"):
        pop_row = pop_df[(pop_df["City"] == "Raleigh")]
    
    if (name == "Richmond"):
        pop_row = pop_df[(pop_df["City"] == "Richmond") & (pop_df["State"] == "Virginia")]
    
    if (name == "Albany"):
        continue
    
    if (name == "Portland"):
        if (temp_row["station_code"] == "KPDX"):
            pop_row = pop_df[(pop_df["City"] == "Portland")]
        else:
            continue
    
    if (name in closest_city and pop_row is None):
        pop_row = pop_df[pop_df["City"].str.match(closest_city[name])]
    elif(pop_row is None):
        pop_row = pop_df[pop_df["City"].str.match(name)]
    
    if (pop_row is None):
        raise Exception("Unknown City")
    
    temp_readings = add_known_temp_row(temp_readings, temp_row, pop_row, total_pop)
    
    if (name == "Raleigh/Durham"):
        pop_row = pop_df[(pop_df["City"] == "Durham")]
        temp_readings = add_known_temp_row(temp_readings, temp_row, pop_row, total_pop)
        

new_df.to_csv("temp_all_cities.csv", index=False)

