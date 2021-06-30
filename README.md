# Poulation-Weighted-Daily-Temperature
Code and graphing for the programming contest to create and graph population weighted daily temperatures in US Cities.

The method taken to create the timeseries was to mainly relate each temperature sensor to it's closest city on the 
population data provided. This was an issue with Albany and Portland Maine primarily, as they are far from any other
city in the population data, and two different solutions have been written for that. In the first (main.py) they are 
simply related to the closest city, Springfield Massachusetts and Manchester New Hampshire respectively. In the second,
(main_with_new_lat_lon.py) latitudes and longitudes for these two cities are added to aid in temperature accuracy, although
populations for these cities are not added, and they are used solely as markers to aid in estimating the temperatures
of nearby cities.

The 2nd of these methologies was used to create the data graphed in graphing.ipynb.

Temperatures in cities without readings are estimated based on their three nearest sensors, with a weighting score for
closer sensors to be more impactful. This allows us to estimate the entire population provided in the data, and create a
weighted poulation timeseries from this data. This has the beenfit of allowing cities which are not reoprting their 
temperature daily to have their temperature estimated each day based on nearby cities.

Weighted population was simply solved by dividing a cities popualtion by the total population in the data, and multiplying 
the temperature by this number, and summing it with all other weighted temperatures.

There are two outlier cities that could arguably be dropped, Anchorage Alaska and Honolulu Hawaii, as the distances these cities 
are from nearby sensors make estimations extremely inaccurate, but for the sake of using all data provided they were kept.

For days where next to no temperature readings were taken, there were no days missing with Phoenix Arizona on the ball, but on 
these days the daily average temperature is averaged from the days previous temperature and the following days temperature.
These are shown graphically with black lines in the graphs showing the daily timeseries.

Monthly and Seasonal averages are graphed with both average maxs and mins, aswell as absolute maxs and mins.

Further work would be to create a time lapse heat map of the cities, which would also display which cities had real sensor data,
and which cities were estimating based on nearby cities, and what cities and how far away they were.
