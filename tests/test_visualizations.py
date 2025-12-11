"""
Tests for visualization module
"""

import pandas as pd
import numpy as np
from datetime import datetime


def test_pattern_insights_visualization():
    """Test that pattern insights visualization works"""
    from visualization import create_pattern_insights_map
    
    # Create sample data
    dates = pd.date_range('2019-01-01', '2024-01-01', freq='D')
    sample_data = pd.DataFrame({
        'datetime': dates,
        'pct': np.random.uniform(0.75, 0.85, len(dates)),
        'precip': np.random.uniform(0, 2, len(dates)),
        'snow': np.random.uniform(0, 5, len(dates)),
        'total_alerts': np.random.randint(0, 100, len(dates)),
        'construction_alerts': np.random.randint(0, 20, len(dates)),
        'technical_problem_alerts': np.random.randint(0, 30, len(dates)),
    })
    
    # Test visualization
    fig = create_pattern_insights_map(sample_data)
    
    assert fig is not None, "Visualization should return a figure"
    assert len(fig.data) > 0, "Figure should have data traces"
    
    print("Pattern insights visualization test passed!")


if __name__ == '__main__':
    test_pattern_insights_visualization()
