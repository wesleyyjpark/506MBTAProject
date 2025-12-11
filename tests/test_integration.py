"""
Integration tests 
"""

import pytest
import pandas as pd
import os


def test_data_processing_pipeline():
    """Test that data files can be processed"""
    # Check that data files exist
    data_files = ['data/combined.csv']
    
    for file in data_files:
        if os.path.exists(file):
            df = pd.read_csv(file)
            assert len(df) > 0, f"{file} should have data"
            
            # Basic validation
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                assert df['datetime'].notna().all(), "Datetime should be valid"


def test_visualization_pipeline():
    """Test that visualizations can be created from data"""
    if not os.path.exists('data/combined.csv'):
        pytest.skip("Data file not found")
    
    df = pd.read_csv('data/combined.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    from visualization import create_pattern_insights_map
    
    # Should be able to create visualization
    fig = create_pattern_insights_map(df)
    assert fig is not None
    
    # Should be able to write to HTML
    os.makedirs('output', exist_ok=True)
    output_file = 'output/test_integration.html'
    fig.write_html(output_file)
    assert os.path.exists(output_file), "Output file should be created"
    
    # Cleanup
    if os.path.exists(output_file):
        os.remove(output_file)

