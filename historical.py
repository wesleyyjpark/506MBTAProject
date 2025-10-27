import pandas as pd

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
    reliability()
