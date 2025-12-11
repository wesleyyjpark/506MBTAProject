"""
MBTA LAMP Data Integration

This module downloads and integrates MBTA LAMP (Lightweight Application for 
Measuring Performance) historical data with existing reliability data.

LAMP provides historical subway performance data including:
- Vehicle positions over time
- Schedule adherence metrics
- Headway consistency
- Dwell times
- Service disruptions

Data source: https://performancedata.mbta.com/
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os
from typing import Optional, List
import time


LAMP_BASE_URL = "https://performancedata.mbta.com"
LAMP_SUBWAY_URL = "https://performancedata.mbta.com/lamp/subway-on-time-performance-v1"
LAMP_INDEX_URL = f"{LAMP_SUBWAY_URL}/index.csv"


def download_lamp_index(output_file: str = "data/lamp/index.csv") -> Optional[pd.DataFrame]:
    """
    Download the LAMP index CSV file listing all available service dates.
    
    Args:
        output_file: Path to save the index CSV
        
    Returns:
        DataFrame with available dates or None if failed
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        print(f"Downloading LAMP index from {LAMP_INDEX_URL}...", end=" ")
        response = requests.get(LAMP_INDEX_URL, timeout=30)
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            df = pd.read_csv(output_file)
            print(f"Success ({len(df)} dates available)")
            return df
        else:
            print(f"Failed (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def download_lamp_subway_data(date: str, output_dir: str = "data/lamp") -> Optional[str]:
    """
    Download LAMP subway performance data for a specific date.
    
    Args:
        date: Date string in YYYY-MM-DD format
        output_dir: Directory to save downloaded files
        
    Returns:
        Path to downloaded file or None if failed
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Correct LAMP URL pattern
    url = f"{LAMP_SUBWAY_URL}/{date}-subway-on-time-performance-v1.parquet"
    
    output_path = os.path.join(output_dir, f"subway_{date}.parquet")
    
    # Skip if already downloaded
    if os.path.exists(output_path):
        print(f"Already exists: {date}")
        return output_path
    
    try:
        print(f"Downloading {date}...", end=" ")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print("Success")
            return output_path
        else:
            print(f"Failed (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def download_lamp_data_range(start_date: str, end_date: str, 
                            output_dir: str = "data/lamp",
                            sample_days: Optional[int] = None) -> List[str]:
    """
    Download LAMP data for a date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_dir: Output directory
        sample_days: If provided, only download every Nth day (for testing)
        
    Returns:
        List of downloaded file paths
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    date_range = pd.date_range(start, end, freq='D')
    
    if sample_days:
        date_range = date_range[::sample_days]
    
    print(f"Downloading LAMP data for {len(date_range)} days ({start_date} to {end_date})")
    print("=" * 60)
    
    downloaded_files = []
    
    for date in date_range:
        date_str = date.strftime('%Y-%m-%d')
        file_path = download_lamp_subway_data(date_str, output_dir)
        if file_path:
            downloaded_files.append(file_path)
        
        # Be nice to the server
        time.sleep(0.5)
    
    print(f"\nDownloaded {len(downloaded_files)} files")
    return downloaded_files


def load_lamp_data(file_paths: List[str]) -> pd.DataFrame:
    """
    Load and combine multiple LAMP data files.
    
    Args:
        file_paths: List of Parquet file paths
        
    Returns:
        Combined DataFrame
    """
    print(f"Loading {len(file_paths)} LAMP data files...")
    
    dfs = []
    for file_path in file_paths:
        try:
            df = pd.read_parquet(file_path)
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Error loading {file_path}: {e}")
    
    if not dfs:
        print("No data loaded")
        return pd.DataFrame()
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(combined)} records")
    
    return combined


def process_lamp_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process LAMP data to extract useful features.
    
    Args:
        df: Raw LAMP DataFrame
        
    Returns:
        Processed DataFrame with extracted features
    """
    if df.empty:
        return df
    
    processed = df.copy()
    
    # Convert service_date (stored as integer YYYYMMDD, e.g., 20240115)
    if 'service_date' in processed.columns:
        # Check if it's integer format (YYYYMMDD)
        if processed['service_date'].dtype in [int, 'int64', 'int32']:
            processed['service_date'] = pd.to_datetime(
                processed['service_date'].astype(str),
                format='%Y%m%d',
                errors='coerce'
            )
        else:
            processed['service_date'] = pd.to_datetime(processed['service_date'], errors='coerce')
    
    # Convert other timestamp columns
    timestamp_cols = ['move_timestamp', 'stop_timestamp']
    for col in timestamp_cols:
        if col in processed.columns:
            try:
                # Try Unix timestamp first
                processed[col] = pd.to_datetime(processed[col], unit='s', errors='coerce')
            except:
                processed[col] = pd.to_datetime(processed[col], errors='coerce')
    
    # Extract temporal features from service_date
    if 'service_date' in processed.columns:
        processed['date'] = processed['service_date'].dt.date
        # Extract hour from stop_timestamp if available, otherwise use service_date
        if 'stop_timestamp' in processed.columns:
            processed['hour'] = processed['stop_timestamp'].dt.hour
        else:
            processed['hour'] = processed['service_date'].dt.hour
        processed['day_of_week'] = processed['service_date'].dt.dayofweek
        processed['is_weekday'] = (processed['day_of_week'] < 5).astype(int)
    
    # Filter for Green Line if route column exists
    route_cols = ['route_id', 'route', 'gtfs_route_id']
    for col in route_cols:
        if col in processed.columns:
            processed = processed[processed[col].str.contains('Green', case=False, na=False)]
            break
    
    return processed


def merge_lamp_with_reliability(lamp_df: pd.DataFrame, reliability_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge LAMP performance data with existing reliability data.
    
    Args:
        lamp_df: LAMP performance DataFrame (processed)
        reliability_df: Existing reliability DataFrame (from combined.csv)
        
    Returns:
        Merged DataFrame
    """
    print("Merging LAMP data with reliability data...")
    
    # Ensure date columns match
    if 'date' in lamp_df.columns:
        lamp_df['date'] = pd.to_datetime(lamp_df['date'])
    
    if 'datetime' in reliability_df.columns:
        reliability_df['date'] = pd.to_datetime(reliability_df['datetime']).dt.date
        reliability_df['date'] = pd.to_datetime(reliability_df['date'])
    elif isinstance(reliability_df.index, pd.DatetimeIndex):
        reliability_df['date'] = reliability_df.index.date
        reliability_df['date'] = pd.to_datetime(reliability_df['date'])
    
    # Aggregate LAMP data by date (average across stops/hours)
    if 'hour' in lamp_df.columns:
        # Aggregate by date only (for daily reliability data)
        agg_dict = {}
        numeric_cols = ['travel_time_seconds', 'dwell_time_seconds', 
                       'headway_trunk_seconds', 'headway_branch_seconds']
        for col in numeric_cols:
            if col in lamp_df.columns:
                agg_dict[col] = 'mean'
        
        if agg_dict:
            lamp_daily = lamp_df.groupby('date').agg(agg_dict).reset_index()
        else:
            lamp_daily = lamp_df.groupby('date').first().reset_index()
    else:
        lamp_daily = lamp_df.groupby('date').first().reset_index()
    
    # Merge on date
    merged = reliability_df.merge(
        lamp_daily,
        on='date',
        how='left',
        suffixes=('_reliability', '_lamp')
    )
    
    print(f"Merged data: {len(merged)} rows")
    new_cols = set(merged.columns) - set(reliability_df.columns)
    if new_cols:
        print(f"New columns: {new_cols}")
    else:
        print(f"Warning: No new columns added (check date matching)")
    
    return merged


def get_available_lamp_dates() -> pd.DataFrame:
    """
    Get list of available LAMP data dates from index.
    
    Returns:
        DataFrame with available dates
    """
    index_df = download_lamp_index()
    if index_df is not None and 'service_date' in index_df.columns:
        index_df['service_date'] = pd.to_datetime(index_df['service_date'])
        return index_df
    return pd.DataFrame()


def integrate_lamp_data(
    start_date: str = "2016-01-01",
    end_date: str = "2024-05-28",
    reliability_csv: str = "data/combined.csv",
    output_csv: str = "data/enriched_with_lamp.csv",
    sample_days: Optional[int] = None,
    use_index: bool = True
) -> pd.DataFrame:
    """
    Complete pipeline to download, process, and integrate LAMP data.
    
    Args:
        start_date: Start date for LAMP data
        end_date: End date for LAMP data
        reliability_csv: Path to existing reliability CSV
        output_csv: Path to save enriched data
        sample_days: If provided, sample every Nth day (for testing)
        
    Returns:
        Enriched DataFrame
    """
    print("=" * 60)
    print("MBTA LAMP Data Integration")
    print("=" * 60)
    
    # Step 0: Check available dates (optional)
    if use_index:
        print("\n0. Checking available LAMP dates...")
        available_dates = get_available_lamp_dates()
        if not available_dates.empty:
            print(f"Found {len(available_dates)} available dates")
            print(f"Date range: {available_dates['service_date'].min()} to {available_dates['service_date'].max()}")
    
    # Step 1: Download LAMP data
    print("\n1. Downloading LAMP data...")
    lamp_files = download_lamp_data_range(
        start_date, end_date,
        sample_days=sample_days
    )
    
    if not lamp_files:
        print("\nWarning: No LAMP files downloaded. Using existing reliability data only.")
        df = pd.read_csv(reliability_csv)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    
    # Step 2: Load LAMP data
    print("\n2. Loading LAMP data...")
    lamp_df = load_lamp_data(lamp_files)
    
    if lamp_df.empty:
        print("\nWarning: LAMP data is empty. Using existing reliability data only.")
        df = pd.read_csv(reliability_csv)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    
    # Step 3: Process LAMP data
    print("\n3. Processing LAMP data...")
    lamp_processed = process_lamp_data(lamp_df)
    
    # Step 4: Load reliability data
    print("\n4. Loading reliability data...")
    reliability_df = pd.read_csv(reliability_csv)
    reliability_df['datetime'] = pd.to_datetime(reliability_df['datetime'])
    
    # Step 5: Merge
    print("\n5. Merging datasets...")
    enriched_df = merge_lamp_with_reliability(lamp_processed, reliability_df)
    
    # Step 6: Save
    print(f"\n6. Saving enriched data to {output_csv}...")
    enriched_df.to_csv(output_csv, index=False)
    print("Complete!")
    
    return enriched_df


if __name__ == '__main__':
    # Example usage
    # For testing, use sample_days=30 to download every 30th day
    # For full dataset, set sample_days=None
    
    print("MBTA LAMP Data Integration Test")
    print("=" * 60)
    
    # First, check available dates
    print("\n1. Checking available dates...")
    available = get_available_lamp_dates()
    if not available.empty:
        print(f"{len(available)} dates available")
        print(f"Range: {available['service_date'].min()} to {available['service_date'].max()}")
        
        # Show sample dates
        print(f"\nSample dates:")
        for date in available['service_date'].head(5):
            print(f"  - {date.strftime('%Y-%m-%d')}")
    
    # Test download with a recent date
    print("\n2. Testing download with a sample date...")
    test_date = "2024-01-15"
    test_file = download_lamp_subway_data(test_date)
    
    if test_file and os.path.exists(test_file):
        print(f"Downloaded: {test_file}")
        try:
            test_df = pd.read_parquet(test_file)
            print(f"Loaded {len(test_df)} rows")
            print(f"Columns: {list(test_df.columns)[:10]}...")
        except Exception as e:
            print(f"Warning: Error loading parquet: {e}")
    else:
        print(f"Warning: Could not download {test_date}")
        print("Note: Date may not be available or URL may need adjustment")
    
    print("\n" + "=" * 60)
    print("To integrate with your data, run:")
    print("  df = integrate_lamp_data(start_date='2024-01-01', end_date='2024-01-31', sample_days=7)")
    print("=" * 60)

