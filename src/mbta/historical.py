import re
import pandas as pd

def process_reliability_data():
    """Reformat the date in the reliability data to be YYYY-MM-DD and compute
    the average pct per day
    """
    pattern = re.compile(r'(\d{4})/(\d{2})/(\d{2}).+')
    df = pd.read_csv('./data/reliability_processed.csv')

    # date format: 2024/05/27 04:00:00+00
    def processor(value: str):
        match = pattern.match(value)
        if not match:
            raise RuntimeError(f'Invalid value: {value}')

        year, month, day = match.groups()
        return f'{year}-{month}-{day}'

    df['datetime'] = df['service_date'].map(processor)
    avg_pct = df.groupby('datetime')['pct'].mean()
    avg_pct.to_csv('./data/reliability2.csv')


def reliability():
    """Process the MBTA reliability data by extracting only the things we need
    """
    df = pd.read_csv('./data/reliability.csv')

    df = df[df['gtfs_route_id'] == 'Green-B']
    df = df[df['metric_type'] == 'Passenger Wait Time']

    df = df[['service_date', 'otp_numerator', 'otp_denominator', 'peak_offpeak_ind']]

    df['pct'] = df['otp_numerator'] / df['otp_denominator']
    df.drop(['otp_numerator', 'otp_denominator'], inplace=True, axis=1)
    print(df)

    df.to_csv('data/reliability_processed.csv', index=False)

if __name__ == '__main__':
    process_reliability_data()
