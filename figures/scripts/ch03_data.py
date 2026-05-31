"""第3章 データローダ

通底ランニング例 (邦画80本) を data/running_example.csv から読み込む.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = ROOT / 'data' / 'running_example.csv'


def load_movies() -> pd.DataFrame:
    """80本邦画データを返す.

    columns: movie_id, genre, has_source, budget, views_30d,
             rec_impressions, rating_count, avg_rating, runtime_min
    """
    return pd.read_csv(CSV_PATH)


if __name__ == '__main__':
    df = load_movies()
    print(df.head())
    print()
    print(df.describe(include='all'))
