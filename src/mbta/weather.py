import os
import pandas as pd
from dotenv import load_dotenv
import requests

def process_weather_data():
    """Given the downloaded weather data, select only the columns we need
    """
    df = pd.read_csv('./data/weather.csv')
    df = df[['datetime', 'precip', 'precipcover', 'preciptype', 'snow', 'snowdepth']]
    print(df)
    df.to_csv('./data/weather_processed.csv', index=False)

def get_weather_data():
    """Download weather data from Visual Crossing and save it into a CSV file
    """
    weather_key = os.getenv('WEATHER_KEY')

    start_date_str = '2016-01-01'
    end_date_str = '2024-05-28'
    url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/boston/{start_date_str}/{end_date_str}'

    params = {
        "key": weather_key,
        "include": "days",
        "contentType": 'csv'
    }

    with requests.get(url, params=params) as resp:
        if resp.status_code != 200:
            print(resp.text)
            return

        with open('data/weather.csv', 'wb') as file:
            for line in resp.iter_lines():
                file.write(line + b"\n")

if __name__ == '__main__':
    load_dotenv()
    process_weather_data()
