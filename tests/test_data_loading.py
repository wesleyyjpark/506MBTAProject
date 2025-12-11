"""
Tests for data loading and processing
"""

import pytest
import pandas as pd
import os


def test_combined_data_exists():
    """Test that combined.csv exists and is readable"""
    assert os.path.exists('data/combined.csv'), "combined.csv should exist"
    
    df = pd.read_csv('data/combined.csv')
    assert len(df) > 0, "Data should have rows"
    assert 'datetime' in df.columns, "Should have datetime column"
    assert 'pct' in df.columns, "Should have pct (reliability) column"


def test_combined_data_structure():
    """Test data structure and types"""
    df = pd.read_csv('data/combined.csv')
    
    # Check required columns
    required_cols = ['datetime', 'pct']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    df['datetime'] = pd.to_datetime(df['datetime'])
    assert df['pct'].dtype in [float, 'float64'], "pct should be numeric"
    
    # Check data ranges
    assert df['pct'].min() >= 0, "Reliability should be >= 0"
    assert df['pct'].max() <= 1, "Reliability should be <= 1"


def test_class_schedules_load():
    """Test that class schedules module loads"""
    from src.mbta.class_schedules import STANDARD_PATTERNS, get_class_starts_at_time
    
    assert len(STANDARD_PATTERNS) > 0, "Should have class patterns"
    
    # Test function
    count = get_class_starts_at_time(10, 10, 0)  # Monday 10:10 AM
    assert isinstance(count, int), "Should return integer"
    assert count >= 0, "Count should be non-negative"

