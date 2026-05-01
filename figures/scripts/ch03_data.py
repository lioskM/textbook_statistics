"""第3章 仮データローダー

通底データセット(コンテンツ人気度/評価テーマ)が確定するまでの暫定データ.
本番データに切り替えるときは load_products() を差し替える.
"""
import numpy as np
import pandas as pd


def load_products(seed: int = 42) -> pd.DataFrame:
    """20商品の仮データを返す.

    Returns
    -------
    pd.DataFrame
        columns: category (str), reviews (int), stars (float), purchases (int)
        4カテゴリ × 各5商品 = 20行
    """
    rng = np.random.default_rng(seed)
    n = 20
    categories = np.repeat(['家電', '書籍', 'ファッション', '食品'], 5)

    # レビュー数: 右に裾を引く (log-normal)
    reviews = np.round(rng.lognormal(mean=3.5, sigma=1.0, size=n)).astype(int)

    # 星評価: 3.0〜5.0 を 0.5 刻み
    stars = np.round(rng.uniform(3.0, 5.0, size=n) * 2) / 2

    # 購買数: レビュー数と相関 + カテゴリ水準差 + 星評価の影響 + ノイズ
    cat_offset = {'家電': 30, '書籍': 10, 'ファッション': 20, '食品': 50}
    purchases = np.array([
        int(max(1, 0.4 * r + cat_offset[c] + rng.normal(0, 8) + (s - 4) * 5))
        for r, c, s in zip(reviews, categories, stars)
    ])

    return pd.DataFrame({
        'category': categories,
        'reviews': reviews,
        'stars': stars,
        'purchases': purchases,
    })


if __name__ == '__main__':
    df = load_products()
    print(df)
    print()
    print(df.describe())
