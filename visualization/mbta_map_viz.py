"""
Pattern Insights Visualization

Creates comprehensive visualizations showing discovered patterns in MBTA reliability data.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.model import create_features, train_model
from src.mbta.stop_names import get_stop_names_batch


def create_pattern_insights_map(df: pd.DataFrame, model_result: Optional[Dict] = None) -> go.Figure:
    """
    Create comprehensive pattern insights visualization.
    
    Shows:
    - Seasonal patterns (monthly reliability)
    - Day of week patterns
    - Weather impact (snow vs reliability)
    - Alert patterns
    - Feature importance
    - Correlation heatmap
    """
    plot_df = df.copy()
    plot_df['datetime'] = pd.to_datetime(plot_df['datetime'])
    
    # Create features if needed
    if 'day_of_week' not in plot_df.columns:
        plot_df = create_features(plot_df)
    
    # Train model if needed
    if model_result is None:
        print("Training model for pattern analysis...")
        model_result = train_model(plot_df)
    
    # Get feature importance
    importances = model_result['reg_importances']
    feature_names = model_result['feature_names']
    top_indices = np.argsort(importances)[-10:][::-1]
    top_features = [feature_names[i] for i in top_indices]
    top_importances = [importances[i] for i in top_indices]
    
    # Prepare data for visualizations
    plot_df['month'] = plot_df['datetime'].dt.month
    plot_df['day_of_week'] = plot_df['datetime'].dt.dayofweek
    plot_df['year'] = plot_df['datetime'].dt.year
    
    # Monthly patterns
    monthly_avg = plot_df.groupby('month').agg({
        'pct': 'mean',
        'snow': 'mean',
        'total_alerts': 'mean',
        'precip': 'mean'
    }).reset_index()
    monthly_avg['month_name'] = pd.to_datetime(monthly_avg['month'], format='%m').dt.strftime('%b')
    
    # Day of week patterns
    dow_avg = plot_df.groupby('day_of_week').agg({
        'pct': 'mean',
        'total_alerts': 'mean',
        'total_class_starts': 'mean'
    }).reset_index()
    dow_avg['day_name'] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Snow vs reliability scatter
    snow_reliability = plot_df[plot_df['snow'] > 0].copy()
    
    # Create comprehensive subplot
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Reliability by Month (Seasonal Pattern)',
            'Reliability by Day of Week',
            'Snow Impact on Reliability',
            'Alert Patterns by Month',
            'Top 10 Predictive Features',
            'Feature Importance Distribution'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. Monthly reliability (line chart)
    fig.add_trace(
        go.Scatter(
            x=monthly_avg['month_name'],
            y=monthly_avg['pct'],
            mode='lines+markers',
            name='Reliability',
            line=dict(color='blue', width=3),
            marker=dict(size=10, color='blue')
        ),
        row=1, col=1
    )
    
    # Add reference line for average
    avg_reliability = plot_df['pct'].mean()
    fig.add_hline(
        y=avg_reliability,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Average: {avg_reliability:.1%}",
        row=1, col=1
    )
    
    # 2. Day of week reliability
    fig.add_trace(
        go.Bar(
            x=dow_avg['day_name'],
            y=dow_avg['pct'],
            name='Reliability',
            marker_color=['#1f77b4', '#1f77b4', '#1f77b4', '#1f77b4', '#1f77b4', '#ff7f0e', '#ff7f0e'],
            text=[f'{p:.1%}' for p in dow_avg['pct']],
            textposition='auto'
        ),
        row=1, col=2
    )
    
    # 3. Snow impact scatter
    if len(snow_reliability) > 0:
        fig.add_trace(
            go.Scatter(
                x=snow_reliability['snow'],
                y=snow_reliability['pct'],
                mode='markers',
                name='Snow Days',
                marker=dict(
                    color=snow_reliability['pct'],
                    colorscale='RdYlGn',
                    size=8,
                    opacity=0.6,
                    showscale=True,
                    colorbar=dict(title="Reliability", x=1.02)
                )
            ),
            row=2, col=1
        )
        
        # Add trend line
        z = np.polyfit(snow_reliability['snow'], snow_reliability['pct'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(snow_reliability['snow'].min(), snow_reliability['snow'].max(), 100)
        fig.add_trace(
            go.Scatter(
                x=x_trend,
                y=p(x_trend),
                mode='lines',
                name='Trend',
                line=dict(color='red', width=2, dash='dash')
            ),
            row=2, col=1
        )
    else:
        fig.add_annotation(
            text="No snow days in dataset",
            xref="x3", yref="y3",
            x=0.5, y=0.5,
            showarrow=False,
            row=2, col=1
        )
    
    # 4. Alert patterns by month
    fig.add_trace(
        go.Bar(
            x=monthly_avg['month_name'],
            y=monthly_avg['total_alerts'],
            name='Alerts',
            marker_color='orange',
            text=[f'{int(a)}' for a in monthly_avg['total_alerts']],
            textposition='auto'
        ),
        row=2, col=2
    )
    
    # 5. Top 10 features (horizontal bar)
    fig.add_trace(
        go.Bar(
            x=top_importances,
            y=top_features,
            orientation='h',
            name='Importance',
            marker_color='green',
            text=[f'{imp:.3f}' for imp in top_importances],
            textposition='auto'
        ),
        row=3, col=1
    )
    
    # 6. Feature importance distribution
    fig.add_trace(
        go.Bar(
            x=list(range(len(top_features))),
            y=top_importances,
            name='Importance',
            marker_color='lightgreen',
            text=[f'{imp:.3f}' for imp in top_importances],
            textposition='auto'
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'MBTA Reliability Pattern Insights<br><sub>Discovering what drives reliability patterns</sub>',
            'x': 0.5,
            'xanchor': 'center'
        },
        height=1200,
        showlegend=False,
        template='plotly_white'
    )
    
    # Update axes
    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Day of Week", row=1, col=2)
    fig.update_xaxes(title_text="Snow (inches)", row=2, col=1)
    fig.update_xaxes(title_text="Month", row=2, col=2)
    fig.update_xaxes(title_text="Importance", row=3, col=1)
    fig.update_xaxes(title_text="Feature Rank", row=3, col=2)
    
    fig.update_yaxes(title_text="Reliability", row=1, col=1, range=[0.7, 0.9])
    fig.update_yaxes(title_text="Reliability", row=1, col=2, range=[0.7, 0.9])
    fig.update_yaxes(title_text="Reliability", row=2, col=1, range=[0.5, 1.0])
    fig.update_yaxes(title_text="Avg Alerts", row=2, col=2)
    fig.update_yaxes(title_text="Feature", row=3, col=1)
    fig.update_yaxes(title_text="Importance", row=3, col=2)
    
    return fig


def create_station_heatmap(
    alerts_file: str = "data/lamp/alerts.parquet",
    reliability_df: Optional[pd.DataFrame] = None,
    top_n_stations: int = 30
) -> go.Figure:
    """
    Create a heatmap showing alert frequency by Green Line station.
    
    Uses LAMP alerts data to show which stations have the most service disruptions.
    This helps identify problematic stations on the Green Line.
    
    Args:
        alerts_file: Path to LAMP alerts parquet file
        reliability_df: Optional reliability DataFrame to merge with
        top_n_stations: Number of top stations to show
        
    Returns:
        Plotly figure with station heatmap
    """
    import os
    
    if not os.path.exists(alerts_file):
        print(f"Alerts file not found: {alerts_file}")
        print("Run 'make data' to download alerts data")
        return None
    
    # Load alerts data
    print(f"Loading alerts data from {alerts_file}...")
    alerts_df = pd.read_parquet(alerts_file)
    
    # Filter for Green Line
    green_mask = alerts_df['informed_entity.route_id'].str.contains('Green', case=False, na=False)
    green_alerts = alerts_df[green_mask].copy()
    
    if green_alerts.empty:
        print("No Green Line alerts found")
        return None
    
    # Extract date and stop
    if 'active_period.start_datetime' in green_alerts.columns:
        green_alerts['date'] = pd.to_datetime(green_alerts['active_period.start_datetime']).dt.date
        green_alerts['date'] = pd.to_datetime(green_alerts['date'])
    elif 'created_datetime' in green_alerts.columns:
        green_alerts['date'] = pd.to_datetime(green_alerts['created_datetime']).dt.date
        green_alerts['date'] = pd.to_datetime(green_alerts['date'])
    else:
        print("No datetime column found in alerts data")
        return None
    
    # Get stop IDs
    green_alerts = green_alerts[green_alerts['informed_entity.stop_id'].notna()].copy()
    
    # Aggregate alerts by stop and date
    stop_daily = green_alerts.groupby(['informed_entity.stop_id', 'date']).size().reset_index(name='alert_count')
    
    # Get top N stations by total alerts
    top_stops = stop_daily.groupby('informed_entity.stop_id')['alert_count'].sum().nlargest(top_n_stations).index
    
    # Filter to top stops
    stop_daily_top = stop_daily[stop_daily['informed_entity.stop_id'].isin(top_stops)].copy()
    
    # Pivot for heatmap: stations (rows) x dates (columns)
    # Use monthly aggregation for better visualization
    stop_daily_top['year_month'] = stop_daily_top['date'].dt.to_period('M').astype(str)
    
    monthly_heatmap = stop_daily_top.groupby(['informed_entity.stop_id', 'year_month'])['alert_count'].sum().reset_index()
    heatmap_pivot = monthly_heatmap.pivot(index='informed_entity.stop_id', columns='year_month', values='alert_count').fillna(0)
    
    # Sort stations by total alerts (descending)
    station_totals = heatmap_pivot.sum(axis=1).sort_values(ascending=False)
    heatmap_pivot = heatmap_pivot.loc[station_totals.index]
    
    # Get stop names
    print("Fetching stop names...")
    stop_names = get_stop_names_batch(list(heatmap_pivot.index), cache_file="data/stop_names_cache.json")
    station_labels = [stop_names.get(stop_id, f"Stop {stop_id}") for stop_id in heatmap_pivot.index]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=station_labels,
        colorscale='Reds',
        colorbar=dict(title="Alert Count"),
        hovertemplate='Station: %{y}<br>Month: %{x}<br>Alerts: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Green Line Station Alert Heatmap<br><sub>Top {top_n_stations} stations by alert frequency (monthly)</sub>',
        xaxis_title='Month',
        yaxis_title='Station',
        height=max(600, len(heatmap_pivot) * 20),
        template='plotly_white'
    )
    
    return fig


def create_crowding_heatmap(
    lamp_data_dir: str = "data/lamp",
    top_n_stations: int = 30
) -> go.Figure:
    """
    Create a heatmap showing average dwell time (crowding proxy) by Green Line station.
    
    Uses LAMP performance data - dwell_time_seconds is a proxy for crowding:
    longer dwell times indicate more passengers boarding/alighting.
    
    Args:
        lamp_data_dir: Directory containing LAMP performance parquet files
        top_n_stations: Number of top stations to show
        
    Returns:
        Plotly figure with crowding heatmap
    """
    import glob
    
    # Find LAMP performance files (exclude alerts.parquet)
    lamp_files = [f for f in glob.glob(f"{lamp_data_dir}/*.parquet") if 'alerts' not in f]
    
    if not lamp_files:
        print(f"No LAMP performance files found in {lamp_data_dir}")
        print("Run 'make data' to download LAMP data")
        return None
    
    print(f"Loading LAMP performance data from {len(lamp_files)} files...")
    
    # Load and combine LAMP data
    dfs = []
    for file in lamp_files[:10]:  # Limit to first 10 files for performance
        try:
            df = pd.read_parquet(file)
            if 'stop_id' in df.columns and 'dwell_time_seconds' in df.columns:
                dfs.append(df[['stop_id', 'service_date', 'dwell_time_seconds', 'route_id']])
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not dfs:
        print("No valid LAMP performance data found")
        return None
    
    lamp_df = pd.concat(dfs, ignore_index=True)
    
    # Filter for Green Line
    if 'route_id' in lamp_df.columns:
        green_mask = lamp_df['route_id'].str.contains('Green', case=False, na=False)
        lamp_df = lamp_df[green_mask].copy()
    
    if lamp_df.empty:
        print("No Green Line data found")
        return None
    
    # Convert service_date
    if lamp_df['service_date'].dtype in [int, 'int64', 'int32']:
        lamp_df['date'] = pd.to_datetime(lamp_df['service_date'].astype(str), format='%Y%m%d', errors='coerce')
    else:
        lamp_df['date'] = pd.to_datetime(lamp_df['service_date'], errors='coerce')
    
    # Filter valid data
    lamp_df = lamp_df[
        lamp_df['stop_id'].notna() & 
        lamp_df['dwell_time_seconds'].notna() & 
        lamp_df['date'].notna()
    ].copy()
    
    # Aggregate average dwell time by stop and date
    stop_daily = lamp_df.groupby(['stop_id', 'date'])['dwell_time_seconds'].mean().reset_index(name='avg_dwell')
    
    # Get top N stations by average dwell time
    top_stops = stop_daily.groupby('stop_id')['avg_dwell'].mean().nlargest(top_n_stations).index
    
    # Filter to top stops
    stop_daily_top = stop_daily[stop_daily['stop_id'].isin(top_stops)].copy()
    
    # Use monthly aggregation for better visualization
    stop_daily_top['year_month'] = stop_daily_top['date'].dt.to_period('M').astype(str)
    
    monthly_heatmap = stop_daily_top.groupby(['stop_id', 'year_month'])['avg_dwell'].mean().reset_index()
    heatmap_pivot = monthly_heatmap.pivot(index='stop_id', columns='year_month', values='avg_dwell').fillna(0)
    
    # Sort stations by total average dwell time (descending)
    station_totals = heatmap_pivot.mean(axis=1).sort_values(ascending=False)
    heatmap_pivot = heatmap_pivot.loc[station_totals.index]
    
    # Get stop names
    print("Fetching stop names...")
    stop_names = get_stop_names_batch(list(heatmap_pivot.index), cache_file="data/stop_names_cache.json")
    station_labels = [stop_names.get(stop_id, f"Stop {stop_id}") for stop_id in heatmap_pivot.index]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=station_labels,
        colorscale='YlOrRd',
        colorbar=dict(title="Avg Dwell Time (seconds)"),
        hovertemplate='Station: %{y}<br>Month: %{x}<br>Avg Dwell: %{z:.1f}s<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Green Line Station Crowding Heatmap<br><sub>Top {top_n_stations} stations by average dwell time (monthly)<br>Longer dwell = more crowding</sub>',
        xaxis_title='Month',
        yaxis_title='Station',
        height=max(600, len(heatmap_pivot) * 20),
        template='plotly_white'
    )
    
    return fig


if __name__ == '__main__':
    print("Pattern Insights Visualization")
    print("=" * 60)
    print("\nThis module creates comprehensive pattern visualizations.")
    print("\nExample usage:")
    print("  from visualization import create_pattern_insights_map, create_station_heatmap, create_crowding_heatmap")
    print("  df = pd.read_csv('data/with_alerts.csv')")
    print("  fig = create_pattern_insights_map(df)")
    print("  fig.show()")
    print("\n  # Station alert heatmap:")
    print("  fig2 = create_station_heatmap()")
    print("  fig2.show()")
    print("\n  # Station crowding heatmap:")
    print("  fig3 = create_crowding_heatmap()")
    print("  fig3.show()")
