"""
MBTA LAMP Alerts Data Integration
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime
from io import BytesIO
from typing import Optional
import os


LAMP_ALERTS_URL = "https://performancedata.mbta.com/lamp/tableau/alerts/LAMP_RT_ALERTS.parquet"

# Green Line route IDs
GREEN_LINE_ROUTES = ['Green-B', 'Green-C', 'Green-D', 'Green-E', 'Green']

# BU-area stop IDs (approximate - may need adjustment)
BU_STOPS = [
    'place-bland',  # Blandford Street
    'place-buest',  # BU East
    'place-buwst',  # BU West
    'place-babck',  # Babcock Street
]


def download_lamp_alerts(output_file: str = "data/lamp/alerts.parquet") -> Optional[pd.DataFrame]:
    """
    Download LAMP alerts data.
    
    Args:
        output_file: Path to save the alerts parquet file
        
    Returns:
        DataFrame with alerts data or None if failed
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Check if already downloaded
    if os.path.exists(output_file):
        print(f"Loading existing alerts data from {output_file}...")
        try:
            return pd.read_parquet(output_file)
        except Exception as e:
            print(f"Error loading existing file: {e}")
            print("Re-downloading...")
    
    try:
        print(f"Downloading LAMP alerts data from {LAMP_ALERTS_URL}...")
        print("(This may take a minute - file is ~4M rows)")
        
        response = requests.get(LAMP_ALERTS_URL, timeout=120)
        
        if response.status_code == 200:
            # Save to file
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            # Load and return
            df = pd.read_parquet(output_file)
            print(f"Success! Downloaded {len(df):,} alert records")
            return df
        else:
            print(f"Failed (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def process_alerts_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process alerts data to extract useful features for predictive modeling.
    
    Args:
        df: Raw alerts DataFrame
        
    Returns:
        Processed DataFrame with date and alert features
    """
    if df.empty:
        return df
    
    processed = df.copy()
    
    # Convert datetime columns
    datetime_cols = ['created_datetime', 'active_period.start_datetime', 
                     'active_period.end_datetime', 'closed_datetime']
    
    for col in datetime_cols:
        if col in processed.columns:
            processed[col] = pd.to_datetime(processed[col], errors='coerce')
    
    # Extract date from active period start (when alert was active)
    if 'active_period.start_datetime' in processed.columns:
        processed['date'] = pd.to_datetime(processed['active_period.start_datetime']).dt.date
        processed['date'] = pd.to_datetime(processed['date'])
    elif 'created_datetime' in processed.columns:
        processed['date'] = pd.to_datetime(processed['created_datetime']).dt.date
        processed['date'] = pd.to_datetime(processed['date'])
    else:
        print("Warning: No datetime column found for date extraction")
        return pd.DataFrame()
    
    # Extract hour from active period start
    if 'active_period.start_datetime' in processed.columns:
        processed['hour'] = pd.to_datetime(processed['active_period.start_datetime']).dt.hour
    elif 'created_datetime' in processed.columns:
        processed['hour'] = pd.to_datetime(processed['created_datetime']).dt.hour
    
    # Filter for Green Line if route information available
    if 'informed_entity.route_id' in processed.columns:
        # Filter for Green Line routes
        green_mask = processed['informed_entity.route_id'].str.contains(
            '|'.join(GREEN_LINE_ROUTES), case=False, na=False
        )
        processed = processed[green_mask].copy()
        print(f"Filtered to Green Line alerts: {len(processed):,} records")
    
    return processed


def extract_daily_alert_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract daily aggregated alert features for predictive modeling.
    
    Args:
        df: Processed alerts DataFrame
        
    Returns:
        DataFrame with daily alert features
    """
    if df.empty or 'date' not in df.columns:
        return pd.DataFrame()
    
    print("Extracting daily alert features...")
    
    # Group by date
    daily_features = []
    
    for date, group in df.groupby('date'):
        features = {'date': date}
        
        # Total alerts
        features['total_alerts'] = len(group)
        
        # Effect-based counts
        if 'effect' in group.columns:
            effects = group['effect'].value_counts()
            features['delays_alerts'] = effects.get('SIGNIFICANT_DELAYS', 0)
            features['no_service_alerts'] = effects.get('NO_SERVICE', 0)
            features['reduced_service_alerts'] = effects.get('REDUCED_SERVICE', 0)
            features['detour_alerts'] = effects.get('DETOUR', 0)
            features['stop_moved_alerts'] = effects.get('STOP_MOVED', 0)
        
        # Cause-based counts
        if 'cause' in group.columns:
            causes = group['cause'].value_counts()
            features['construction_alerts'] = causes.get('CONSTRUCTION', 0)
            features['maintenance_alerts'] = causes.get('MAINTENANCE', 0)
            features['technical_problem_alerts'] = causes.get('TECHNICAL_PROBLEM', 0)
            features['weather_alerts'] = causes.get('WEATHER', 0)
            features['accident_alerts'] = causes.get('ACCIDENT', 0)
            features['police_activity_alerts'] = causes.get('POLICE_ACTIVITY', 0)
        
        # Severity features
        if 'severity' in group.columns:
            features['max_severity'] = group['severity'].max() if not group['severity'].isna().all() else 0
            features['avg_severity'] = group['severity'].mean() if not group['severity'].isna().all() else 0
            features['high_severity_alerts'] = (group['severity'] >= 7).sum() if not group['severity'].isna().all() else 0
        
        # Duration features (if available)
        if 'active_period.start_datetime' in group.columns and 'active_period.end_datetime' in group.columns:
            durations = (
                pd.to_datetime(group['active_period.end_datetime']) - 
                pd.to_datetime(group['active_period.start_datetime'])
            ).dt.total_seconds() / 60  # Convert to minutes
            
            features['total_alert_duration_minutes'] = durations.sum() if not durations.isna().all() else 0
            features['avg_alert_duration_minutes'] = durations.mean() if not durations.isna().all() else 0
            features['max_alert_duration_minutes'] = durations.max() if not durations.isna().all() else 0
        
        # Stop-specific features (BU area stops)
        if 'informed_entity.stop_id' in group.columns:
            bu_stops_alerts = group['informed_entity.stop_id'].isin(BU_STOPS).sum()
            features['bu_area_alerts'] = bu_stops_alerts
        
        daily_features.append(features)
    
    daily_df = pd.DataFrame(daily_features)
    
    if not daily_df.empty:
        print(f"Extracted features for {len(daily_df)} days")
        print(f"Date range: {daily_df['date'].min()} to {daily_df['date'].max()}")
    
    return daily_df


def extract_time_specific_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract time-specific alert features (rush hours, class end times).
    
    Args:
        df: Processed alerts DataFrame
        
    Returns:
        DataFrame with time-specific features
    """
    if df.empty or 'date' not in df.columns or 'hour' not in df.columns:
        return pd.DataFrame()
    
    print("Extracting time-specific alert features...")
    
    # Define time periods
    morning_rush = (df['hour'] >= 7) & (df['hour'] <= 9)
    afternoon_rush = (df['hour'] >= 16) & (df['hour'] <= 18)
    class_end_times = (df['hour'] >= 9) & (df['hour'] <= 11) | (df['hour'] >= 13) & (df['hour'] <= 15)
    
    time_features = []
    
    for date, group in df.groupby('date'):
        features = {'date': date}
        
        # Rush hour alerts
        morning_group = group[morning_rush[group.index] if len(group) > 0 else []]
        afternoon_group = group[afternoon_rush[group.index] if len(group) > 0 else []]
        class_end_group = group[class_end_times[group.index] if len(group) > 0 else []]
        
        features['morning_rush_alerts'] = len(morning_group) if len(morning_group) > 0 else 0
        features['afternoon_rush_alerts'] = len(afternoon_group) if len(afternoon_group) > 0 else 0
        features['class_end_time_alerts'] = len(class_end_group) if len(class_end_group) > 0 else 0
        
        # Rush hour delays
        if 'effect' in group.columns:
            features['morning_rush_delays'] = (morning_group['effect'] == 'SIGNIFICANT_DELAYS').sum() if len(morning_group) > 0 else 0
            features['afternoon_rush_delays'] = (afternoon_group['effect'] == 'SIGNIFICANT_DELAYS').sum() if len(afternoon_group) > 0 else 0
        
        time_features.append(features)
    
    time_df = pd.DataFrame(time_features)
    
    if not time_df.empty:
        print(f"Extracted time-specific features for {len(time_df)} days")
    
    return time_df


def merge_alerts_with_reliability(
    alerts_daily: pd.DataFrame,
    reliability_csv: str = "data/combined.csv"
) -> pd.DataFrame:
    """
    Merge daily alert features with reliability data.
    
    Args:
        alerts_daily: Daily aggregated alert features
        reliability_csv: Path to reliability CSV
        
    Returns:
        Merged DataFrame
    """
    print("Merging alerts data with reliability data...")
    
    # Load reliability data
    reliability_df = pd.read_csv(reliability_csv)
    reliability_df['datetime'] = pd.to_datetime(reliability_df['datetime'])
    reliability_df['date'] = reliability_df['datetime'].dt.date
    reliability_df['date'] = pd.to_datetime(reliability_df['date'])
    
    # Ensure alerts date is datetime
    if 'date' in alerts_daily.columns:
        alerts_daily['date'] = pd.to_datetime(alerts_daily['date'])
    
    # Merge on date
    merged = reliability_df.merge(
        alerts_daily,
        on='date',
        how='left',
        suffixes=('_reliability', '_alerts')
    )
    
    # Fill missing alert values with 0 (no alerts = 0)
    alert_cols = [col for col in merged.columns if 'alert' in col.lower() or 'severity' in col.lower()]
    for col in alert_cols:
        merged[col] = merged[col].fillna(0)
    
    print(f"Merged data: {len(merged)} rows")
    new_cols = set(merged.columns) - set(reliability_df.columns)
    if new_cols:
        print(f"New alert columns added: {len(new_cols)}")
        print(f"Sample: {list(new_cols)[:10]}")
    
    return merged


def integrate_alerts_data(
    reliability_csv: str = "data/combined.csv",
    output_csv: str = "data/with_alerts.csv",
    alerts_cache: str = "data/lamp/alerts.parquet"
) -> pd.DataFrame:
    """
    Complete pipeline to download, process, and integrate alerts data.
    
    Args:
        reliability_csv: Path to existing reliability CSV
        output_csv: Path to save enriched data
        alerts_cache: Path to cache alerts data
        
    Returns:
        Enriched DataFrame
    """
    print("=" * 60)
    print("MBTA LAMP Alerts Data Integration")
    print("=" * 60)
    print("Purpose: Pattern learning for predictive crowding forecasts")
    print()
    
    # Step 1: Download alerts data
    print("1. Downloading/loading alerts data...")
    alerts_df = download_lamp_alerts(alerts_cache)
    
    if alerts_df is None or alerts_df.empty:
        print("Warning: No alerts data available. Using existing reliability data only.")
        df = pd.read_csv(reliability_csv)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    
    print(f"   Loaded {len(alerts_df):,} alert records")
    
    # Step 2: Process alerts data
    print("\n2. Processing alerts data...")
    alerts_processed = process_alerts_data(alerts_df)
    
    if alerts_processed.empty:
        print("Warning: Processed alerts data is empty. Using existing reliability data only.")
        df = pd.read_csv(reliability_csv)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    
    # Step 3: Extract daily features
    print("\n3. Extracting daily alert features...")
    alerts_daily = extract_daily_alert_features(alerts_processed)
    
    if alerts_daily.empty:
        print("Warning: No daily features extracted. Using existing reliability data only.")
        df = pd.read_csv(reliability_csv)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    
    # Step 4: Extract time-specific features
    print("\n4. Extracting time-specific features...")
    alerts_time = extract_time_specific_features(alerts_processed)
    
    if not alerts_time.empty:
        # Merge time features with daily features
        alerts_daily = alerts_daily.merge(alerts_time, on='date', how='left')
        # Fill missing time features with 0
        time_cols = [col for col in alerts_time.columns if col != 'date']
        for col in time_cols:
            alerts_daily[col] = alerts_daily[col].fillna(0)
    
    # Step 5: Merge with reliability data
    print("\n5. Merging with reliability data...")
    enriched_df = merge_alerts_with_reliability(alerts_daily, reliability_csv)
    
    # Step 6: Save
    print(f"\n6. Saving enriched data to {output_csv}...")
    enriched_df.to_csv(output_csv, index=False)
    print("Complete!")
    
    # Summary
    print("\n" + "=" * 60)
    print("Integration Summary")
    print("=" * 60)
    alert_cols = [col for col in enriched_df.columns if 'alert' in col.lower() or 'severity' in col.lower()]
    print(f"Total rows: {len(enriched_df):,}")
    print(f"Rows with alert data: {enriched_df[alert_cols[0]].notna().sum() if alert_cols else 0}")
    print(f"Alert features added: {len(alert_cols)}")
    
    return enriched_df


if __name__ == "__main__":
    # Run integration
    df = integrate_alerts_data()
    print(f"\nEnriched dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

