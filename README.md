# 506MBTAProject
## Project Repository for CS5066

### Project Description:
Students at specific stops and times significantly contribute to MBTA train delays. We would like to predict surges in passenger volume on the MBTA Green Line to create a tool that students can use while commuting. 
Our goal is to identify to a high degree of accuracy, transit crowd hotspots in real time and visualize it as a map that can be used to avoid/plan when to take the T.


## Midterm Report 

### Youtube Link 
[Midterm Report Video](https://youtu.be/MnIV4ef9FLM?si=AImOTgxgkv5k4gZe)

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
- **Linear Regression Models**: 
  - Single variable (precipitation only): R² = -0.0011 (essentially no predictive power)
  - Multiple variables (precip, precipcover, snow, snowdepth): R² = 0.0368 (explains only ~3.7% of variance)
  
- **K-Means Clustering**: 
  - Identified 4 distinct weather clusters (Clear, Rain, Snow, Snowpack)
  - Identified 3 reliability clusters (Low, Medium, High)
  - Cross-tabulated weather and reliability to find patterns
  - **Key Finding**: Weather alone is a weak predictor of transit reliability

- **Correlation Analysis**:
  - Precipitation vs Reliability: r = -0.0308
  - Snow vs Reliability: r = -0.1833
  - Both correlations are very weak

### Data visualization methods
- **Time Series Analysis**: Plotted reliability trends from 2016-2024, showing month-by-month and day-of-week patterns
- **Scatter Plots**: Analyzed relationships between weather variables (precipitation, snow) and reliability
- **Correlation Heatmap**: Visualized correlations between all weather variables and reliability
- **Cluster Visualizations**: 
  - 2D plots showing weather clusters (precipitation vs snow)
  - Box plots comparing reliability distributions across clusters
  - Heatmaps showing probability distributions


### Preliminary results
- **Weather is NOT the main driver of reliability**: Daily weather patterns explain only ~3.7% of reliability variation (R² = 0.0368)
- **Clustering reveals 4 weather types**:
  - Cluster 0 (Clear days): 83% of days, avg reliability = 79.8%
  - Cluster 1 (Rainy days): 12% of days, avg reliability = 79.5%
  - Cluster 2 (Heavy snow): 1.2% of days (38 days), avg reliability = 73.2%
  - Cluster 3 (Deep snowpack): 3.7% of days, avg reliability = 78.1%
- **Reliability distribution**: 
  - High reliability (>84%): 36.9% of days
  - Medium reliability (75-84%): 45.4% of days
  - Low reliability (<75%): 17.7% of days
- There is high variability in reliability (σ = 0.048), but weather alone cannot explain this variability. 

### Next
- Integrate class schedule data and more specific periods of time besides the day itself
- Utilize the MBTA real-time API to gather crowdedness data and look at relationship between it and weather/schedules 

### Datasets
- [Transit Reliability](https://mbta-massdot.opendata.arcgis.com/datasets/MassDOT::mbta-bus-commuter-rail-rapid-transit-reliability/about)