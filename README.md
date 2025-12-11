# 506MBTAProject
## Project Repository for CS5066

**CS 506 Final Project**

Video:


## Project Overview

This project aims to predict when the Green Line will have reliability issues and identify crowding hotspots, so students can plan their commutes better.

**The Problem**: Students at specific stops and times significantly contribute to MBTA train delays. We wanted to predict surges in passenger volume on the MBTA Green Line and create a tool that students can use while commuting.

**The Goal**: Identify transit crowd hotspots with high accuracy and visualize them so students can avoid delays and plan when to take the T.

---

## How to Build and Run

### Prerequisites
- Python 3.9+
- pip
- A Visual Crossing API key (free tier works fine)


1. **Install dependencies:**
   ```bash
   make install
   # Or manually: pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```
   WEATHER_KEY=your_visual_crossing_api_key
   MBTA_API_KEY=your_mbta_api_key  # Optional, for stop name lookups
   ```

4. **Download reliability data:**
   - Go to [MBTA ArcGIS OpenData](https://mbta-massdot.opendata.arcgis.com/datasets/MassDOT::mbta-bus-commuter-rail-rapid-transit-reliability/about)
   - Download the data and save as `data/reliability.csv`

5. **Run the full pipeline:**
   ```bash
   make all
   ```
   This will: install dependencies → download/process data → run tests → generate visualizations

### Step-by-Step Commands

**Process data:**
```bash
make data
```
This downloads weather data, processes reliability data, merges datasets, and integrates LAMP alerts data.

**Train the model:**
```bash
python -m src.models.model
```
Shows model results including the 70.6% classification accuracy.

**Generate visualizations:**
```bash
make visualize
```
Creates three interactive HTML visualizations:
- `output/pattern_insights.html` - Comprehensive pattern analysis dashboard
- `output/station_heatmap.html` - Alert frequency by station
- `output/crowding_heatmap.html` - Crowding (dwell time) by station

**Run tests:**
```bash
make test
```

**Clean generated files:**
```bash
make clean
```

### Project Structure

```
506MBTAProject/
├── src/                   # Source code
│   ├── mbta/              # MBTA data processing
│   │   ├── class_schedules.py    # BU class schedule patterns
│   │   ├── historical.py         # Reliability data processing
│   │   ├── weather.py            # Weather data processing
│   │   ├── merging.py            # Data merging pipeline
│   │   ├── mbta.py              # MBTA API utilities
│   │   └── stop_names.py        # Stop ID to name mapping
│   ├── models/            # Modeling code
│   │   ├── feature_engineering.py  # Feature creation (119 features)
│   │   └── model.py               # Final model (Random Forest)
│   └── integration/      # Data integration
│       ├── lamp_data_integration.py   # LAMP performance data
│       └── lamp_alerts_integration.py # LAMP alerts data
├── scripts/               # Utility scripts
│   └── download_more_lamp_data.py
├── notebooks/             # Analysis notebooks
│   └── analysis.ipynb
├── visualization/         # Interactive visualizations
│   └── mbta_map_viz.py
├── tests/                 # Test files
├── output/                # Generated visualizations
├── data/                  # Data files (cleaned CSVs included, raw data excluded)
├── Makefile               # Build automation
├── requirements.txt       # Python dependencies
└── README.md              # This file
```



## Project Timeline: What I Tried and What Worked

### Initial Exploration

**What I did:**
- Started with just MBTA reliability data and weather data
- Tried simple linear regression with weather features only
- Did some basic clustering to understand patterns

**Results:**
- Weather-only model: R² = 0.0368 (only 3.7% of variance explained!)
- Key finding: Weather alone is NOT a good predictor of reliability
- Clustering showed 4 weather types but weak correlation with reliability

**What I learned:**
- Need more data sources
- Need to think about temporal patterns, not just current weather

### Phase 2: Adding More Data (Weeks 3-4)

**What I did:**
- Integrated MBTA LAMP performance data (headway, dwell time, travel time)
- Added BU class schedule patterns (MWF vs TR, peak class times)
- Created temporal features (day of week, month, hour)

**Results:**
- With LAMP features: R² = -0.4649 (severe overfitting!)
- The model was memorizing training data instead of learning patterns
- Realized I needed better feature engineering

**What I learned:**
- More features ≠ better model
- Need proper train/test splits (temporal splitting!)
- Overfitting is a real problem

### Phase 3: Advanced Feature Engineering (Weeks 5-6)

**What I did:**
- Created 119 features including:
  - Time-series features (lagged values, rolling averages)
  - Interaction features (weather × class schedules)
  - Alert pattern features (from LAMP alerts data)
  - Snow volatility and rolling averages

**Results:**
- Random Forest with all 119 features: R² = -0.50 (still overfitting!)
- Ridge Regression: R² = -2.68 (even worse!)
- Too many features made things worse

**What I learned:**
- Feature selection is crucial
- Need to be more selective about which features matter
- Mutual information can help identify important features

### Phase 4: Focused Approach (Weeks 7-8)

**What I did:**
- Reduced to ~25 carefully selected features
- Used mutual information for feature selection
- Tried different model types (Random Forest, Ridge, Gradient Boosting)

**Results:**
- Random Forest: R² = -0.22 (best so far, but still negative)
- Ridge Regression: R² = -0.26
- Still overfitting, but getting better

**What I learned:**
- Regression might not be the right approach
- Predicting exact percentages is really hard
- Maybe classification would work better?

### Phase 5: The Breakthrough - Classification (Weeks 9-10)

**What I did:**
- Switched from regression to classification
- Instead of predicting exact reliability %, predict categories: High/Medium/Low
- Used Random Forest Classifier with 20 selected features
- Proper temporal splitting (train on 2019-2022, test on 2023-2024)

**Results:**

**What I did:**
- Created comprehensive visualizations
- Added station-level heatmaps (alerts and crowding)
- Integrated stop name mapping (so stations show actual names, not IDs)
- Made everything reproducible with Makefile

**Results:**
- Visualizations
- Students can actually use these to plan commutes
- Project is complete and reproducible

---

## Final Results

### Model Performance

**Best Model: Random Forest Classifier**
- **Accuracy: 70.6%** (predicting High/Medium/Low reliability)
- Model: Random Forest with 300 trees, max_depth=6
- Features: 20 selected using mutual information
- Train/Test Split: Temporal (2019-2022 train, 2023-2024 test)

**Top 5 Predictive Features:**
1. Month (0.102) - Strong seasonal patterns
2. Snow rolling 3-day average (0.093) - Recent snow patterns matter
3. Snow volatility (0.091) - Snow std over 7 days
4. Alert frequency (0.083) - Days since last alert
5. Alert patterns (0.070) - Monthly alert patterns

### What we found

1. **Weather alone explains only 3.7% of reliability variance**
   - Weather is not the main factor of reliability issues.

2. **Seasonal patterns**
   - Month is the #1 predictor
   - Winter months (Jan-Feb) have lower reliability
   - This makes sense - snow, cold weather, more disruptions

3. **Snow patterns**
   - Recent snow (3-day average) is more predictive than today's snow
   - Snow volatility (how much it varies) is also important

4. **Alert frequency**
   - Stations with recent alerts are more likely to have reliability issues
   - Pattern learning from alerts helps predict future problems

5. **Time-series**
   - Lag features and rolling averages capture important patterns
   - Simple features miss these temporal relationships

### What Didn't Work

- **Linear regression**: Too simple, couldn't capture non-linear patterns
- **Too many features**: 119 features caused severe overfitting
- **Regression approach**: Predicting exact percentages was too hard
- **Ignoring temporal structure**: train/test splits were bad

### What Worked

- **Classification instead of regression**: Predicting categories is more reliable
- **Feature selection**: Mutual information helped identify the 20 most important features
- **Time-series features**: Lag features and rolling averages capture important patterns
- **Random Forest**: Handles non-linear relationships and feature interactions well

---

## Data Sources

### Collected Data

1. **MBTA Reliability Data** (2016-2024)
   - Source: [MBTA ArcGIS OpenData](https://mbta-massdot.opendata.arcgis.com/datasets/MassDOT::mbta-bus-commuter-rail-rapid-transit-reliability/about)
   - Contains: Daily reliability percentages for Green Line B
   - Manual download required

2. **Weather Data** (2016-2024)
   - Source: [Visual Crossing API](https://www.visualcrossing.com/)
   - Contains: Precipitation, snow, temperature, humidity, etc.
   - Downloaded automatically via `make data`

3. **BU Class Schedule Patterns**
   - Source: BU standard class meeting times
   - Contains: MWF and TR class start times (8am, 10am, 12pm, 2pm, 4pm)
   - Encoded in `src/mbta/class_schedules.py`

4. **MBTA LAMP Performance Data** (2019-2024)
   - Source: [MBTA Performance Data Portal](https://performancedata.mbta.com/)
   - Contains: Headway, dwell time, travel time metrics
   - Downloaded automatically via `make data`

5. **MBTA LAMP Alerts Data** (2019-2025)
   - Source: MBTA LAMP alerts system
   - Contains: 4.1M alert records (construction, maintenance, technical problems)
   - Downloaded automatically via `make data`

### Data Processing

- Standardized datetime formats across all datasets
- Handled missing values (filled with zeros where appropriate)
- Filtered for Green Line routes only
- Aggregated to daily level (since reliability data is daily)
- Created temporal features (day of week, month, hour)
- Merged all datasets on date

---

## Feature Engineering

Created 119 features total, then selected the top 20 using mutual information:

### Feature Categories

1. **Temporal Features**
   - Day of week, month, hour
   - is_weekend, is_monday
   - Semester patterns (fall/spring/summer)

2. **Weather Features**
   - Current: precip, snow, snowdepth
   - Lagged: snow_lag_1d, snow_lag_7d
   - Rolling averages: snow_rolling_3d, snow_rolling_7d
   - Volatility: snow_std_7d

3. **Class Schedule Features**
   - Morning class starts (8am-10am)
   - Afternoon class starts (12pm-3pm)
   - Total class starts per day

4. **Alert Features**
   - Daily counts: construction_alerts, technical_problem_alerts, total_alerts
   - Lagged: total_alerts_lag_1d, total_alerts_lag_7d
   - Rolling averages: total_alerts_rolling_7d, total_alerts_rolling_14d
   - Patterns: alert_pattern_month, days_since_last_alert

5. **Interaction Features**
   - snow_x_classes (snow × class starts)
   - alerts_x_classes (alerts × class starts)

### Feature Selection

Used mutual information to select the top 20 features. This helped reduce overfitting and improve model performance.

---

## Visualizations

### 1. Pattern Viz
Shows patterns across:
- Monthly reliability trends (seasonal patterns)
- Day-of-week patterns (weekday vs weekend)
- Snow impact analysis (scatter plot with trend line)
- Alert patterns by month
- Top 10 feature importance
- Feature importance distribution

Validates that month is the #1 predictor and shows why winter months have lower reliability.

### 2. Station Alert Heatmap
Shows which stations have the most service disruptions:
- Top 30 stations by alert frequency
- Monthly aggregation
- Uses actual station names (not just IDs)
- Darker colors = more alerts

Identifies problematic stations where students might want to avoid boarding.

### 3. Station Crowding Heatmap
Shows which stations have the most crowding:
- Top 30 stations by average dwell time
- Monthly aggregation
- Dwell time = proxy for passenger volume
- Uses actual station names

Directly addresses the original goal of predicting passenger volume surges.

All visualizations are interactive HTML files that can be opened in any browser.

---

## Testing

- Data loading and structure
- Feature engineering functions
- Visualization creation
- Integration pipeline

Run tests with:
```bash
make test
```