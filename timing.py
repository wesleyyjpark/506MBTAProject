import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression

def main():
  df = pd.read_csv('./data/reliability2.csv')

  def mapper(entry: str):
    value = datetime.strptime(entry, '%Y-%m-%d')
    return pd.Series({
      # 'day': value.day,
      'month': value.month,
      'year': value.year
    })

  df[['month', 'year']] = df['datetime'].apply(mapper)

  # calculate average reliability by year
  means = df.groupby(['year', 'month'])['pct'].mean()

  with open('timings.csv', 'w') as file:
    file.write('year,month,pct\n')
    for i in range(len(means)):
      month = i % 12
      year = i // 12

      file.write(f'{2016 + year},{month + 1},{means.values[i]}\n')

def process_timings():
  df = pd.read_csv('./data/timings.csv', index_col="month")
  df.sort_index(inplace=True)
  df.to_csv('./data/timings2.csv')
  print(df.head())

if __name__ == '__main__':
  process_timings()