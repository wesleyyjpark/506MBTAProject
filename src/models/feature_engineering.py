"""
Feature Engineering for MBTA Reliability Prediction
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.mbta.class_schedules import get_class_starts_in_window, get_class_starts_at_time


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add temporal features (day of week, month, etc.)"""
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['month'] = df['datetime'].dt.month
    df['day_of_month'] = df['datetime'].dt.day
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_monday'] = (df['day_of_week'] == 0).astype(int)
    df['is_friday'] = (df['day_of_week'] == 4).astype(int)
    
    # Semester patterns (approximate)
    df['is_fall_semester'] = df['month'].isin([9, 10, 11, 12]).astype(int)
    df['is_spring_semester'] = df['month'].isin([1, 2, 3, 4, 5]).astype(int)
    df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
    
    return df


def add_class_schedule_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add class schedule features based on day of week"""
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Get day of week (0=Monday, 6=Sunday)
    df['day_of_week'] = df['datetime'].dt.dayofweek
    
    # Morning rush class starts (8:00-10:00)
    df['morning_class_starts'] = df.apply(
        lambda row: get_class_starts_in_window(8, 0, 10, 0, row['day_of_week']) 
        if row['day_of_week'] < 5 else 0, axis=1
    )
    
    # Midday class starts (10:00-12:00)
    df['midday_class_starts'] = df.apply(
        lambda row: get_class_starts_in_window(10, 0, 12, 0, row['day_of_week']) 
        if row['day_of_week'] < 5 else 0, axis=1
    )
    
    # Afternoon class starts (12:00-15:00)
    df['afternoon_class_starts'] = df.apply(
        lambda row: get_class_starts_in_window(12, 0, 15, 0, row['day_of_week']) 
        if row['day_of_week'] < 5 else 0, axis=1
    )
    
    # Evening class starts (15:00-18:00)
    df['evening_class_starts'] = df.apply(
        lambda row: get_class_starts_in_window(15, 0, 18, 0, row['day_of_week']) 
        if row['day_of_week'] < 5 else 0, axis=1
    )
    
    # Total class starts per day
    df['total_class_starts'] = (
        df['morning_class_starts'] + 
        df['midday_class_starts'] + 
        df['afternoon_class_starts'] + 
        df['evening_class_starts']
    )
    
    # Peak class times (most common start times)
    # MWF patterns: 9:05, 10:10, 12:20, 13:25, 14:30
    # TR patterns: 8:00, 9:30, 11:00, 12:30, 14:00, 15:30, 17:00
    df['is_mwf_day'] = df['day_of_week'].isin([0, 2, 4]).astype(int)  # Mon, Wed, Fri
    df['is_tr_day'] = df['day_of_week'].isin([1, 3]).astype(int)  # Tue, Thu
    
    return df


def add_time_series_features(df: pd.DataFrame, lag_days: list = [1, 2, 3, 7]) -> pd.DataFrame:
    """Time-series features
    
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Lag features for predictors (NOT target variable to avoid leakage)
    for lag in lag_days:
        df[f'precip_lag_{lag}d'] = df['precip'].shift(lag)
        df[f'snow_lag_{lag}d'] = df['snow'].shift(lag)
        df[f'total_alerts_lag_{lag}d'] = df['total_alerts'].shift(lag)
        df[f'construction_alerts_lag_{lag}d'] = df['construction_alerts'].shift(lag)
        df[f'technical_problem_alerts_lag_{lag}d'] = df['technical_problem_alerts'].shift(lag)
    
    # Rolling averages 
    for window in [3, 7, 14]:
        df[f'precip_rolling_{window}d'] = df['precip'].rolling(window=window, min_periods=1).mean()
        df[f'snow_rolling_{window}d'] = df['snow'].rolling(window=window, min_periods=1).mean()
        df[f'total_alerts_rolling_{window}d'] = df['total_alerts'].rolling(window=window, min_periods=1).mean()
    
    # Rolling standard deviations 
    for window in [7, 14]:
        df[f'precip_std_{window}d'] = df['precip'].rolling(window=window, min_periods=1).std()
        df[f'snow_std_{window}d'] = df['snow'].rolling(window=window, min_periods=1).std()
    
    return df


def add_alert_pattern_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add pattern learning features for alerts (when alerts typically occur)"""
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Day-of-week alert patterns (rolling average by day of week)
    for day in range(7):
        day_mask = df['day_of_week'] == day
        df[f'alert_pattern_dow_{day}'] = 0.0
        if day_mask.sum() > 0:
            # Calculate average alerts for this day of week over time
            df.loc[day_mask, f'alert_pattern_dow_{day}'] = (
                df.loc[day_mask, 'total_alerts'].expanding().mean()
            )
    
    # Monthly alert patterns
    for month in range(1, 13):
        month_mask = df['month'] == month
        df[f'alert_pattern_month_{month}'] = 0.0
        if month_mask.sum() > 0:
            df.loc[month_mask, f'alert_pattern_month_{month}'] = (
                df.loc[month_mask, 'total_alerts'].expanding().mean()
            )
    
    # Alert frequency (days since last alert)
    df['days_since_last_alert'] = (
        df.groupby((df['total_alerts'] > 0).cumsum()).cumcount()
    )
    
    # Alert streak (consecutive days with alerts)
    df['alert_streak'] = (
        (df['total_alerts'] > 0).groupby((df['total_alerts'] > 0).ne((df['total_alerts'] > 0).shift()).cumsum()).cumsum()
    )
    
    return df


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interaction features (alerts × schedules × weather × temporal)"""
    df = df.copy()
    
    # Alerts × Day of Week interactions
    df['alerts_x_monday'] = df['total_alerts'] * df['is_monday']
    df['alerts_x_friday'] = df['total_alerts'] * df['is_friday']
    df['alerts_x_weekend'] = df['total_alerts'] * df['is_weekend']
    
    # Alerts × Class Schedules interactions
    df['alerts_x_morning_classes'] = df['total_alerts'] * df['morning_class_starts']
    df['alerts_x_afternoon_classes'] = df['total_alerts'] * df['afternoon_class_starts']
    df['construction_x_class_starts'] = df['construction_alerts'] * df['total_class_starts']
    df['morning_rush_alerts_x_classes'] = df['morning_rush_alerts'] * df['morning_class_starts']
    df['class_end_alerts_x_classes'] = df['class_end_time_alerts'] * df['afternoon_class_starts']
    
    # Weather × Alerts interactions
    df['precip_x_alerts'] = df['precip'] * df['total_alerts']
    df['snow_x_alerts'] = df['snow'] * df['total_alerts']
    df['snow_x_construction'] = df['snow'] * df['construction_alerts']
    df['precip_x_technical_problems'] = df['precip'] * df['technical_problem_alerts']
    
    # Weather × Class Schedules interactions
    df['snow_x_morning_classes'] = df['snow'] * df['morning_class_starts']
    df['precip_x_class_starts'] = df['precip'] * df['total_class_starts']
    
    # Temporal × Alerts interactions
    df['month_x_alerts'] = df['month'] * df['total_alerts']
    df['fall_semester_x_alerts'] = df['is_fall_semester'] * df['total_alerts']
    df['spring_semester_x_alerts'] = df['is_spring_semester'] * df['total_alerts']
    
    # Multi-factor interactions (the key recommendation!)
    df['construction_x_monday_x_classes'] = (
        df['construction_alerts'] * df['is_monday'] * df['morning_class_starts']
    )
    df['snow_x_monday_x_classes'] = (
        df['snow'] * df['is_monday'] * df['morning_class_starts']
    )
    df['alerts_x_weekday_x_classes'] = (
        df['total_alerts'] * (1 - df['is_weekend']) * df['total_class_starts']
    )
    
    return df


def create_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create all features"""
    print("Creating advanced features...")
    print(f"  Starting shape: {df.shape}")
    
    # Temporal features
    print("  Adding temporal features...")
    df = add_temporal_features(df)
    
    # Class schedule features
    print("  Adding class schedule features...")
    df = add_class_schedule_features(df)
    
    # Time-series features
    print("  Adding time-series features...")
    df = add_time_series_features(df)
    
    # Alert pattern features
    print("  Adding alert pattern features...")
    df = add_alert_pattern_features(df)
    
    # Interaction features
    print("  Adding interaction features...")
    df = add_interaction_features(df)
    
    print(f"  Final shape: {df.shape}")
    print(f"  Added {df.shape[1] - len(['datetime', 'pct', 'precip', 'snow', 'total_alerts'])} features")
    
    return df


def get_feature_columns(df: pd.DataFrame, exclude_cols: list = None) -> list:
    """Get list of feature columns for modeling"""
    if exclude_cols is None:
        exclude_cols = ['datetime', 'pct', 'date']
    
    # Exclude non-feature columns
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Remove columns with all NaN or constant values
    feature_cols = [
        col for col in feature_cols 
        if df[col].notna().sum() > 0 and df[col].nunique() > 1
    ]
    
    return feature_cols


if __name__ == '__main__':
    # Load data
    print("Loading data...")
    df = pd.read_csv('data/with_alerts.csv')
    
    # Filter to dates with alerts data (2019+)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[df['datetime'] >= '2019-01-01'].copy()
    
    # Create advanced features
    df_features = create_advanced_features(df)
    
    # Save
    import os
    output_path = os.path.join(os.path.dirname(__file__), '../../data/with_advanced_features.csv')
    df_features.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")
    
    # Show feature summary
    feature_cols = get_feature_columns(df_features)
    print(f"\nTotal features: {len(feature_cols)}")
    print(f"\nFeature categories:")
    print(f"  Temporal: {len([c for c in feature_cols if 'day_of_week' in c or 'month' in c or 'is_' in c])}")
    print(f"  Class schedules: {len([c for c in feature_cols if 'class' in c.lower()])}")
    print(f"  Time-series: {len([c for c in feature_cols if 'lag' in c or 'rolling' in c])}")
    print(f"  Alert patterns: {len([c for c in feature_cols if 'alert_pattern' in c or 'alert_streak' in c])}")
    print(f"  Interactions: {len([c for c in feature_cols if '_x_' in c])}")

