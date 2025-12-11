import pandas as pd

def main():
    reliability_data = pd.read_csv('./data/reliability2.csv')
    weather_data = pd.read_csv('./data/weather_processed.csv')

    final_df = pd.merge(reliability_data, weather_data, on="datetime")
    final_df.set_index('datetime', inplace=True)
    final_df.to_csv('./data/combined.csv')

if __name__ == '__main__':
    main()