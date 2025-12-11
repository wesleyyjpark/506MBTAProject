"""
Download LAMP data for multiple dates to fill in the dataset.
"""

from src.integration.lamp_data_integration import integrate_lamp_data, get_available_lamp_dates
import pandas as pd

print("=" * 60)
print("Downloading LAMP Data for Multiple Dates")
print("=" * 60)

# Check available dates
print("\n1. Checking available LAMP dates...")
available = get_available_lamp_dates()
print(f"{len(available)} dates available")

# Load your data
print("\n2. Loading data...")
rel = pd.read_csv('data/combined.csv')
rel['datetime'] = pd.to_datetime(rel['datetime'])
rel['date'] = rel['datetime'].dt.date

# Find overlap
overlap_start = max(rel['date'].min(), available['service_date'].min().date())
overlap_end = min(rel['date'].max(), available['service_date'].max().date())

print(f"   Your data: {rel['date'].min()} to {rel['date'].max()}")
print(f"   LAMP data: {available['service_date'].min().date()} to {available['service_date'].max().date()}")
print(f"   Overlap: {overlap_start} to {overlap_end}")

# Download options
print("\n" + "=" * 60)
print("Download Options:")
print("=" * 60)
print("\nA) Download weekly samples (every 7th day) - FAST")
print("   ~52 dates per year, good for testing")
print("\nB) Download monthly samples (every 30th day) - MEDIUM")
print("   ~12 dates per year, balanced")
print("\nC) Download all matching dates - SLOW")
print("   Full coverage, will take hours")

print("\n" + "=" * 60)
print("Recommended: Start with weekly samples (option A)")
print("=" * 60)

# Download weekly samples for overlap period
print("\n3. Downloading weekly LAMP data samples...")
print(f"   Date range: {overlap_start} to {overlap_end}")
print("   Sampling: Every 7th day (weekly)")

df = integrate_lamp_data(
    start_date=str(overlap_start),
    end_date=str(overlap_end),
    sample_days=7,  # Weekly samples
    output_csv='data/with_lamp_weekly.csv',
    use_index=True  # Use index to check availability
)

print("\n" + "=" * 60)
print("Download Complete!")
print("=" * 60)

# Check results
merged = pd.read_csv('../data/with_lamp_weekly.csv')
lamp_count = merged['travel_time_seconds'].notna().sum()

print(f"\nResults:")
print(f"  Total rows: {len(merged)}")
print(f"  Rows with LAMP data: {lamp_count}")
print(f"  Coverage: {lamp_count/len(merged)*100:.1f}%")

if lamp_count > 0:
    print(f"\nSuccess! {lamp_count} dates now have LAMP data")
    print(f"File saved: ../data/with_lamp_weekly.csv")
else:
    print("\nWarning: No LAMP data matched. Check date conversion.")

print("\n" + "=" * 60)
print("Next Steps:")
print("=" * 60)
print("1. Use this file for analysis: ../data/with_lamp_weekly.csv")
print("2. To get more coverage, download monthly (sample_days=30)")
print("3. For full coverage, download all dates (sample_days=None)")
print("=" * 60)

