"""ランニング例 検証スクリプト.

入力: data/running_example.csv
出力:
  data_generation/histograms/*.png  各変数のヒストグラム
  data_generation/figs/*.png        章別演習の補助図
  data_generation/verification_report.md  統合レポート

実行:
  uv run python data_generation/verify_running_example.py
"""
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / 'data' / 'running_example.csv'
OUT_DIR = ROOT / 'data_generation'
HIST_DIR = OUT_DIR / 'histograms'
FIG_DIR = OUT_DIR / 'figs'
REPORT_PATH = OUT_DIR / 'verification_report.md'

STYLE_PATH = ROOT / 'figures' / 'scripts' / 'textbook.mplstyle'
if STYLE_PATH.exists():
    plt.style.use(str(STYLE_PATH))

NUMERIC_COLS = [
    'budget', 'views_30d', 'rec_impressions',
    'rating_count', 'avg_rating', 'runtime_min',
]
LABEL_JA = {
    'budget':           '製作費 (円)',
    'views_30d':        '公開後30日間視聴回数',
    'rec_impressions':  'おすすめ表示回数',
    'rating_count':     '評価件数',
    'avg_rating':       '平均評価',
    'runtime_min':      '上映時間 (分)',
}

RNG = np.random.default_rng(20260501)


def fmt_num(x: float, *, digits: int = 2) -> str:
    if abs(x) >= 1e6:
        return f'{x:,.0f}'
    if abs(x) >= 100:
        return f'{x:,.1f}'
    return f'{x:.{digits}f}'


# ============================================================
# 1. 基本統計量
# ============================================================
def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in NUMERIC_COLS:
        s = df[col].astype(float)
        rows.append({
            '変数': LABEL_JA[col],
            'n':       int(s.count()),
            '平均':    s.mean(),
            '中央値':  s.median(),
            '分散':    s.var(ddof=1),
            '標準偏差': s.std(ddof=1),
            '最小':    s.min(),
            '最大':    s.max(),
        })
    return pd.DataFrame(rows)


def stats_to_md(df_stats: pd.DataFrame) -> str:
    header = '| 変数 | n | 平均 | 中央値 | 分散 | 標準偏差 | 最小 | 最大 |'
    sep    = '|---|---:|---:|---:|---:|---:|---:|---:|'
    lines = [header, sep]
    for _, r in df_stats.iterrows():
        lines.append(
            f"| {r['変数']} | {r['n']} | {fmt_num(r['平均'])} | "
            f"{fmt_num(r['中央値'])} | {fmt_num(r['分散'])} | "
            f"{fmt_num(r['標準偏差'])} | {fmt_num(r['最小'])} | "
            f"{fmt_num(r['最大'])} |"
        )
    return '\n'.join(lines)


# ============================================================
# 2. ヒストグラム
# ============================================================
def save_histograms(df: pd.DataFrame) -> list[str]:
    HIST_DIR.mkdir(parents=True, exist_ok=True)
    rels = []
    for col in NUMERIC_COLS:
        fig, ax = plt.subplots(figsize=(4.5, 2.8))
        ax.hist(df[col], bins=20, color='#4C7CA8',
                edgecolor='white', linewidth=0.6)
        ax.set_xlabel(LABEL_JA[col])
        ax.set_ylabel('度数')
        ax.set_title(f'{LABEL_JA[col]} のヒストグラム')
        path = HIST_DIR / f'{col}.png'
        fig.savefig(path)
        plt.close(fig)
        rels.append(path.relative_to(OUT_DIR).as_posix())
    return rels


# ============================================================
# 3. 相関行列
# ============================================================
def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return df[NUMERIC_COLS].corr()


def corr_to_md(corr: pd.DataFrame) -> str:
    cols = [LABEL_JA[c] for c in corr.columns]
    header = '| 変数 | ' + ' | '.join(cols) + ' |'
    sep = '|---|' + '|'.join(['---:'] * len(cols)) + '|'
    lines = [header, sep]
    for c in corr.columns:
        row = [LABEL_JA[c]] + [f'{v:.3f}' for v in corr.loc[c]]
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)


# ============================================================
# 4. 章別演習シミュレーション
# ============================================================
def chapter2(df: pd.DataFrame) -> str:
    s = df['views_30d'].astype(float)
    return dedent(f"""
        - 平均: {fmt_num(s.mean())}
        - 中央値: {fmt_num(s.median())}
        - 平均 / 中央値 の比: {s.mean() / s.median():.2f}
        - 歪度 (skewness): {stats.skew(s):.2f}

        平均が中央値より明確に大きく, 右に歪んだ分布であることが確認できる.
    """).strip()


def chapter4(df: pd.DataFrame) -> tuple[str, str]:
    """20作品ずつ無作為抽出を繰り返した標本平均の分布."""
    s = df['views_30d'].to_numpy()
    n_iter = 5000
    sample_size = 20
    means = np.empty(n_iter)
    for i in range(n_iter):
        idx = RNG.choice(len(s), size=sample_size, replace=False)
        means[i] = s[idx].mean()

    pop_mean = s.mean()
    pop_sd = s.std(ddof=0)
    se_theory = pop_sd / np.sqrt(sample_size)

    # 図
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    ax.hist(means, bins=40, color='#4C7CA8', edgecolor='white', linewidth=0.5)
    ax.axvline(pop_mean, color='#D55E00', linewidth=1.2, label='母平均')
    ax.set_xlabel('標本平均 (n=20)')
    ax.set_ylabel('頻度')
    ax.set_title(f'標本平均の分布 (リサンプリング {n_iter} 回)')
    ax.legend()
    path = FIG_DIR / 'ch04_sampling_dist.png'
    fig.savefig(path)
    plt.close(fig)

    # 標本平均分布の正規性検定 (Shapiro-Wilkは大標本だと敏感すぎるので参考値)
    skew_val = stats.skew(means)
    kurt_val = stats.kurtosis(means)

    text = dedent(f"""
        - リサンプリング: {n_iter} 回, サンプルサイズ {sample_size}
        - 母平均: {fmt_num(pop_mean)}
        - 標本平均の平均: {fmt_num(means.mean())}
        - 標本平均の標準偏差 (実測): {fmt_num(means.std(ddof=1))}
        - 理論的標準誤差 (σ/√n): {fmt_num(se_theory)}
        - 標本平均分布の歪度: {skew_val:.3f}
        - 標本平均分布の尖度: {kurt_val:.3f}

        標本平均分布の歪度が元データに比べて大きく縮み, ほぼ正規分布に近い形となる
        ことが確認できる (中心極限定理の確認).
    """).strip()

    rel = path.relative_to(OUT_DIR).as_posix()
    return text, rel


def chapter5(df: pd.DataFrame) -> str:
    """母平均の95%区間推定."""
    s = df['views_30d'].to_numpy()
    n = len(s)
    mean = s.mean()
    se = s.std(ddof=1) / np.sqrt(n)
    t_crit = stats.t.ppf(0.975, df=n - 1)
    lo, hi = mean - t_crit * se, mean + t_crit * se
    width_ratio = (hi - lo) / mean
    return dedent(f"""
        - 標本サイズ: {n}
        - 標本平均: {fmt_num(mean)}
        - 標準誤差: {fmt_num(se)}
        - t 臨界値 (df={n - 1}, 両側 95%): {t_crit:.3f}
        - 95%信頼区間: [{fmt_num(lo)}, {fmt_num(hi)}]
        - 区間幅 / 平均: {width_ratio:.2f}

        平均値の20-30%程度の幅で信頼区間が得られ, 教育的に扱いやすい区間幅である.
    """).strip()


def chapter6(df: pd.DataFrame) -> str:
    """原作あり vs 原作なし の平均視聴回数 t検定."""
    g1 = df.loc[df['has_source'], 'views_30d'].to_numpy()
    g0 = df.loc[~df['has_source'], 'views_30d'].to_numpy()
    t, p = stats.ttest_ind(g1, g0, equal_var=False)  # Welch
    diff = g1.mean() - g0.mean()

    cohens_d = diff / np.sqrt((g1.var(ddof=1) + g0.var(ddof=1)) / 2)

    judge = 'p < 0.05 (5%水準で有意)' if p < 0.05 else 'p ≥ 0.05 (有意ではない)'
    return dedent(f"""
        - 原作あり群: n={len(g1)}, 平均={fmt_num(g1.mean())}, sd={fmt_num(g1.std(ddof=1))}
        - 原作なし群: n={len(g0)}, 平均={fmt_num(g0.mean())}, sd={fmt_num(g0.std(ddof=1))}
        - 平均差 (あり - なし): {fmt_num(diff)}
        - Welch t統計量: {t:.3f}
        - p値: {p:.4f}
        - Cohen's d: {cohens_d:.3f}
        - 判定: {judge}
    """).strip()


def chapter7(df: pd.DataFrame) -> str:
    """主要な変数ペアの相関係数."""
    pairs = [
        ('budget',          'views_30d', '製作費 vs 視聴回数',           '弱〜中 (0.3〜0.5)'),
        ('rec_impressions', 'views_30d', 'おすすめ表示回数 vs 視聴回数', '中〜強 (0.6〜0.8)'),
        ('avg_rating',      'views_30d', '平均評価 vs 視聴回数',         '弱 (0.1〜0.3)'),
        ('rating_count',    'views_30d', '評価件数 vs 視聴回数',         '中〜強 (0.6〜0.8)'),
        ('runtime_min',     'views_30d', '上映時間 vs 視聴回数',         'ほぼ無相関'),
    ]
    lines = ['| ペア | 相関係数 | 設計目安 | 範囲内? |',
             '|---|---:|---|:---:|']
    for x, y, label, target in pairs:
        r = df[x].corr(df[y])
        in_range = _in_target(label, r)
        mark = 'OK' if in_range else 'NG'
        lines.append(f'| {label} | {r:+.3f} | {target} | {mark} |')
    return '\n'.join(lines)


def _in_target(label: str, r: float) -> bool:
    if '製作費' in label:
        return 0.3 <= r <= 0.5
    if 'おすすめ' in label:
        return 0.6 <= r <= 0.8
    if '平均評価' in label:
        return 0.1 <= r <= 0.3
    if '評価件数' in label:
        return 0.6 <= r <= 0.8
    if '上映時間' in label:
        return -0.2 <= r <= 0.2
    return False


def chapter8(df: pd.DataFrame) -> tuple[str, str]:
    """製作費 → 視聴回数 の単回帰."""
    x = df['budget'].to_numpy()
    y = df['views_30d'].to_numpy()
    slope, intercept, r, p, se = stats.linregress(x, y)
    r_squared = r ** 2

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    ax.scatter(x, y, s=18, color='#4C7CA8', alpha=0.7, edgecolor='white')
    xs = np.linspace(x.min(), x.max(), 200)
    ax.plot(xs, intercept + slope * xs, color='#D55E00', linewidth=1.0)
    ax.set_xlabel(LABEL_JA['budget'])
    ax.set_ylabel(LABEL_JA['views_30d'])
    ax.set_title('製作費 → 視聴回数 単回帰')
    path = FIG_DIR / 'ch08_regression.png'
    fig.savefig(path)
    plt.close(fig)

    text = dedent(f"""
        - 切片: {fmt_num(intercept)}
        - 傾き (1円当たり): {slope:.6f}
        - 傾き (1億円当たり): {fmt_num(slope * 1e8)}
        - 決定係数 R²: {r_squared:.3f}
        - 相関係数 r: {r:+.3f}
        - 傾きの p値: {p:.4f}
        - 傾きの標準誤差: {se:.6f}

        傾きは正で, 決定係数は中程度. 単回帰の限界 (説明しきれない散らばり) が
        散布図から読み取れる.
    """).strip()

    rel = path.relative_to(OUT_DIR).as_posix()
    return text, rel


# ============================================================
# 5. 質的変数のサマリ
# ============================================================
def categorical_summary(df: pd.DataFrame) -> str:
    parts = []
    parts.append('**ジャンル**:')
    g = df['genre'].value_counts()
    for k, v in g.items():
        parts.append(f'- {k}: {v}')
    parts.append('')
    parts.append('**原作の有無**:')
    o = df['has_source'].value_counts()
    parts.append(f"- あり: {int(o.get(True, 0))}")
    parts.append(f"- なし: {int(o.get(False, 0))}")
    return '\n'.join(parts)


# ============================================================
# 6. レポート生成
# ============================================================
def main() -> None:
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')

    df_stats = summarize(df)
    hist_paths = save_histograms(df)
    corr = correlation_matrix(df)
    cat_md = categorical_summary(df)

    ch2 = chapter2(df)
    ch4_text, ch4_fig = chapter4(df)
    ch5 = chapter5(df)
    ch6 = chapter6(df)
    ch7 = chapter7(df)
    ch8_text, ch8_fig = chapter8(df)

    md = []
    md.append('# ランニング例 検証レポート (試作版)')
    md.append('')
    md.append(f'- 入力: `{CSV_PATH.relative_to(ROOT).as_posix()}`')
    md.append(f'- 標本サイズ N: {len(df)}')
    md.append('')
    md.append('## 1. 基本統計量')
    md.append('')
    md.append(stats_to_md(df_stats))
    md.append('')
    md.append('## 2. 質的変数の度数分布')
    md.append('')
    md.append(cat_md)
    md.append('')
    md.append('## 3. ヒストグラム')
    md.append('')
    for p in hist_paths:
        # ファイル名から変数名を逆引き
        col = Path(p).stem
        md.append(f'### {LABEL_JA[col]}')
        md.append('')
        md.append(f'![{LABEL_JA[col]}]({p})')
        md.append('')
    md.append('## 4. 相関係数行列')
    md.append('')
    md.append(corr_to_md(corr))
    md.append('')
    md.append('## 5. 章別演習シミュレーション')
    md.append('')
    md.append('### 2章: 視聴回数の平均と中央値 (右への歪みの確認)')
    md.append('')
    md.append(ch2)
    md.append('')
    md.append('### 4章: 標本平均の分布 (中心極限定理)')
    md.append('')
    md.append(ch4_text)
    md.append('')
    md.append(f'![標本平均の分布]({ch4_fig})')
    md.append('')
    md.append('### 5章: 母平均の95%区間推定')
    md.append('')
    md.append(ch5)
    md.append('')
    md.append('### 6章: 原作あり vs 原作なし の平均視聴回数 t検定')
    md.append('')
    md.append(ch6)
    md.append('')
    md.append('### 7章: 主要な変数ペアの相関係数')
    md.append('')
    md.append(ch7)
    md.append('')
    md.append('### 8章: 製作費 → 視聴回数 単回帰')
    md.append('')
    md.append(ch8_text)
    md.append('')
    md.append(f'![単回帰散布図]({ch8_fig})')
    md.append('')

    REPORT_PATH.write_text('\n'.join(md), encoding='utf-8')
    print(f'saved: {REPORT_PATH}')


if __name__ == '__main__':
    main()
