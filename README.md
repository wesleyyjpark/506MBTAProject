# 506MBTAProject
## Project Repository for CS506

### Project Description:
Students at specific stops and times significantly contribute to MBTA train delays. We would like to predict surges in passenger volume on the MBTA Green Line to create a tool that students can use while commuting. 
Our goal is to identify to a high degree of accuracy, transit crowd hotspots in real time and visualize it as a map that can be used to avoid/plan when to take the T.


## Midterm Report 

### Youtube Link 
[Midterm Report Video](youtube.com)

### Methods of data processing
- Cleaned data from MBTA's OpenData ArcGis to gather the Day and percentage of reliability of the Green Line
- Gathered weather precipitation API data from Visual Crossing to get historical data from 2016 - present, this includes other
currently unused data such as temperature, dew, humidity, and snow. 

|name  |datetime  |tempmax|tempmin|temp|feelslikemax|feelslikemin|feelslike|dew |humidity|precip|precipprob|precipcover|preciptype|snow|snowdepth|windgust|windspeed|winddir|sealevelpressure|cloudcover|visibility|solarradiation|solarenergy|uvindex|severerisk|sunrise            |sunset             |moonphase|conditions|description                     |icon  |stations                    |
|------|----------|-------|-------|----|------------|------------|---------|----|--------|------|----------|-----------|----------|----|---------|--------|---------|-------|----------------|----------|----------|--------------|-----------|-------|----------|-------------------|-------------------|---------|----------|--------------------------------|------|----------------------------|
|boston|2016-01-01|41     |34     |38  |33.8        |22.8        |30.5     |24.7|58.5    |0     |0         |0          |          |0   |0.1      |32.2    |19.3     |257.3  |1013.5          |92.3      |9.8       |84.1          |7.3        |4      |          |2016-01-01T07:13:30|2016-01-01T16:22:08|0.73     |Overcast  |Cloudy skies throughout the day.|cloudy|72509854704,KBOS,72509014739|


- BU policies file including the standard meeting pattern of all classes and schedules was converted to JSON data to be used in
determining student movement and if there is coorelation between class end times and T station surges. 

```json
    {"days": "MWF", "start": "09:05", "end": "09:55", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "10:10", "end": "11:00", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "12:20", "end": "13:10", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "13:25", "end": "14:15", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "14:30", "end": "15:20", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "16:40", "end": "17:30", "duration_min": 50, "type": "A"},
```

- Percentage reliability determiend from the number of person waiting vs schedule adherents 
- Weather data combined with reliability data to determine a coorelation 


### Data modeling methods


### Data visualization methods


### Preliminary results
- We were able to 
(e.g. we fit a linear model to the data and we achieve promising results, or we did some clustering and we notice a clear pattern in the data)

### Datasets
- [Transit Reliability](https://mbta-massdot.opendata.arcgis.com/datasets/MassDOT::mbta-bus-commuter-rail-rapid-transit-reliability/about)