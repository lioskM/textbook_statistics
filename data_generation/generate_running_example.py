"""ランニング例 架空データ生成スクリプト.

設計: docs/データ設計ドキュメント.md / docs/ランニング例設定メモ_v2.md

出力:
  data/running_example.csv

実行:
  uv run python data_generation/generate_running_example.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N = 80

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / 'data' / 'running_example.csv'


def generate(seed: int = SEED, n: int = N) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # ---- 質的変数 ----
    # ジャンル: 5カテゴリ, サンプル数に偏りを持たせる
    genre_choices = ['ヒューマンドラマ', 'サスペンス', 'コメディ', '恋愛', 'アクション']
    genre_probs = [0.30, 0.22, 0.20, 0.15, 0.13]
    genres = rng.choice(genre_choices, size=n, p=genre_probs)

    # 原作の有無: 概ね半々. オリジナル脚本がやや多い
    has_source = rng.choice([True, False], size=n, p=[0.45, 0.55])

    # ---- 潜在因子 ----
    # popularity: 視聴回数を主に駆動する潜在因子 (作品の話題性・知名度)
    popularity = rng.normal(0, 1, n)

    # ---- 製作費 (右に歪んだ分布) ----
    # 中央値 1.5億円, log-scale sigma 0.7. 数千万〜10億円のレンジに収まる
    log_budget_z = rng.normal(0, 1, n)
    log_budget = np.log(1.5e8) + 0.7 * log_budget_z
    budget = np.exp(log_budget)

    # ---- 視聴回数 (公開後30日) ----
    # log_views = base + popularity + 製作費直接効果 + ジャンル + 原作 + ノイズ
    genre_effect_map = {
        'ヒューマンドラマ': 0.00,
        'サスペンス':       0.10,
        'コメディ':         0.15,
        '恋愛':            -0.10,
        'アクション':       0.30,
    }
    genre_effect = np.array([genre_effect_map[g] for g in genres])
    origin_effect = np.where(has_source, 0.75, 0.0)

    log_views = (
        np.log(8e5)
        + 0.72 * popularity
        + 0.55 * log_budget_z
        + genre_effect
        + origin_effect
        + 0.35 * rng.normal(0, 1, n)
    )
    views_30d = np.exp(log_views).astype(int)

    # ---- おすすめ表示回数 ----
    # 視聴回数 × 倍率. 倍率は popularity に弱く依存 + 独立ノイズ.
    # 目安: 視聴回数の数倍 (中央倍率 4-5x).
    log_multiplier = np.log(4.0) + 0.20 * popularity + 0.55 * rng.normal(0, 1, n)
    rec_impressions = (views_30d * np.exp(log_multiplier)).astype(int)

    # ---- 評価件数 ----
    # 視聴回数 × レビュー率. レビュー率の独立ばらつきを大きく取り,
    # 視聴回数との相関が中〜強 (0.65〜0.75) に収まるよう設計.
    log_review_rate = np.log(0.005) + 0.75 * rng.normal(0, 1, n)
    rating_count = np.maximum(5, (views_30d * np.exp(log_review_rate)).astype(int))

    # ---- 平均評価 (1.0-5.0, J字型/高評価寄り) ----
    # ベース: Beta(5, 2) を 1〜5 にスケール (高評価寄り).
    # popularity に弱く依存させ, 視聴回数との弱相関を作る.
    beta_sample = rng.beta(5.0, 2.0, n)
    rating_signal = 0.18 * popularity + 0.10 * rng.normal(0, 1, n)
    avg_rating = 1.0 + 4.0 * beta_sample + rating_signal
    avg_rating = np.clip(avg_rating, 1.0, 5.0)
    avg_rating = np.round(avg_rating, 2)

    # ---- 上映時間 (90-150分, ほぼ対称) ----
    runtime_min = rng.normal(110, 12, n)
    runtime_min = np.clip(runtime_min, 88, 158).round().astype(int)

    df = pd.DataFrame({
        'movie_id':         [f'M{i:03d}' for i in range(1, n + 1)],
        'genre':            genres,
        'has_source':       has_source,
        'budget':           budget.round().astype(int),
        'views_30d':        views_30d,
        'rec_impressions':  rec_impressions,
        'rating_count':     rating_count,
        'avg_rating':       avg_rating,
        'runtime_min':      runtime_min,
    })
    return df


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')
    print(f'saved: {OUT_PATH} ({len(df)} rows)')
    print(df.head())


if __name__ == '__main__':
    main()
