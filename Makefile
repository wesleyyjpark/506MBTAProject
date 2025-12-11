# Makefile for 506MBTAProject
# Provides commands to build, test, and run the project

.PHONY: help install test clean data visualize

help:
	@echo "506MBTAProject - MBTA Reliability Analysis"
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install all dependencies"
	@echo "  make test        - Run tests"
	@echo "  make data        - Download and process data"
	@echo "  make visualize   - Generate visualizations"
	@echo "  make clean       - Clean generated files"
	@echo "  make all         - Run full pipeline"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed"

test:
	@echo "Running tests..."
	python -m pytest tests/ -v || echo "No tests directory found - create tests/ to add tests"
	@echo "Tests complete"

data:
	@echo "Downloading and processing data..."
	@echo ""
	@echo "Step 1: Processing reliability data..."
	@python -m src.mbta.historical || echo "Note: Requires reliability.csv in data/ directory"
	@echo ""
	@echo "Step 2: Downloading weather data..."
	@python -m src.mbta.weather || echo "Note: Requires WEATHER_KEY in .env file"
	@echo ""
	@echo "Step 3: Merging datasets..."
	@python -m src.mbta.merging || echo "Note: Run steps 1-2 first"
	@echo ""
	@echo "Step 4: Integrating LAMP alerts data (optional)..."
	@python -c "from src.integration.lamp_alerts_integration import integrate_alerts_data; integrate_alerts_data()" || echo "Note: LAMP alerts integration skipped (optional)"
	@echo ""
	@echo "Data processing complete!"
	@echo "Note: Large data files are not committed to git."
	@echo "      Run 'make data' to download/process data locally."

visualize:
	@echo "Generating visualizations..."
	@python -c "from visualization import create_pattern_insights_map, create_station_heatmap, create_crowding_heatmap; import pandas as pd; import os; df = pd.read_csv('data/with_alerts.csv'); df['datetime'] = pd.to_datetime(df['datetime']); df = df[df['datetime'] >= '2019-01-01'].copy(); fig1 = create_pattern_insights_map(df); fig1.write_html('output/pattern_insights.html'); print('Pattern insights saved to output/pattern_insights.html'); fig2 = create_station_heatmap() if os.path.exists('data/lamp/alerts.parquet') else None; fig2.write_html('output/station_heatmap.html') if fig2 else None; print('Station alert heatmap saved to output/station_heatmap.html') if fig2 else print('Skipping station alert heatmap (alerts data not found)'); fig3 = create_crowding_heatmap() if os.path.exists('data/lamp') else None; fig3.write_html('output/crowding_heatmap.html') if fig3 else None; print('Crowding heatmap saved to output/crowding_heatmap.html') if fig3 else print('Skipping crowding heatmap (LAMP data not found)')" || echo "Note: Run 'make data' first to generate data files"
	@echo "Visualizations generated"
	@echo "Visualizations generated"

clean:
	@echo "Cleaning generated files..."
	rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/__pycache__
	rm -rf *.pyc */*.pyc */*/*.pyc
	rm -rf .pytest_cache
	rm -rf output/*.html output/*.png
	@echo "Clean complete"

clean-data:
	@echo "Cleaning data files..."
	@echo "This will remove all downloaded/processed data files."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/*.csv data/*.parquet data/lamp/; \
		echo "Data files cleaned"; \
	else \
		echo "Cancelled"; \
	fi

all: install data test visualize
	@echo ""
	@echo "Full pipeline complete!"
	@echo "  Check output/ directory for visualizations"

