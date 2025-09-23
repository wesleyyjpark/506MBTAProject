# 506MBTAProject
Project Repository for CS506

Proposal:
Description: 
Students at specific stops and times significantly contribute to MBTA train delays. I would like to predict surges in passenger volume on the MBTA Green Line. 
Goal:
Identify to a high degree of accuracy, transit crowd hotspots in real time and visualize it as a map that can be used to avoid/plan when to take the T.

This means being able to predict
  Where/when congestion is likely to spike
  If a station is likely to be overcrowded or a train delayed
  How these surges affect other stops along the Green Line
  
Data:
- MBTA API Data (v3 API)
- Real-time train positions
- Headways and delays
- Station stop times
- University Class Schedule Time Tables
- Weather API

Data modeling:
Create a student crowd pressure score:
- Based on student travel estimates
- Adjusted by weather and events and class times
Model it as a time series classification or regression:
- Classification: Will this station experience a surge in X amount of time
- Regression: How high will the score be?
  
Visualization:
Potential ideas:
Interactive MBTA map with Mapbox?
- Live crowd pressure scores at each station
Time-series plots:
- Surge score over day/week
Heatmaps:
- Surge level vs. time of day, weather, and  class start times
- 
Test plan:
Time-based split:
- Train the model on the first 3 weeks of data in a given month (probably September for data we already have)
- Test it on the next week to see prediction and accuracy
