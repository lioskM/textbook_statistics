"""第3章 図生成スクリプト

生成される図:
  - ch03_histogram.pdf : レビュー数のヒストグラム (ビン幅3パターン)
  - ch03_boxplot.pdf   : カテゴリ別購買数の箱ひげ図
  - ch03_scatter.pdf   : レビュー数 × 購買数の散布図 (星評価で離散色分け)

連続カラーバー版の散布図は試作で不採用. 必要になれば別途作成.

実行:
  cd figures/scripts && python ch03.py
出力:
  figures/output/ch03_*.pdf, ch03_*.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from ch03_data import load_products

# パス
SCRIPT_DIR = Path(__file__).resolve().parent
OUTDIR = SCRIPT_DIR.parent / 'output'
OUTDIR.mkdir(exist_ok=True)

# スタイル適用
plt.style.use(str(SCRIPT_DIR / 'textbook.mplstyle'))


def save(fig, name: str):
    """PDF と PNG の両方で保存."""
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png')
    plt.close(fig)
    print(f'saved: {name}')


# ------- データ -------
df = load_products()


# ============================================================
# 図3.3: レビュー数ヒストグラム ビン幅3パターン
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4), sharey=True)
bin_specs = [(4, 'ビン幅 大'), (8, 'ビン幅 中'), (16, 'ビン幅 小')]
for ax, (n_bins, label) in zip(axes, bin_specs):
    ax.hist(df['reviews'], bins=n_bins, color='#4C7CA8',
            edgecolor='white', linewidth=0.6)
    ax.set_title(label)
    ax.set_xlabel('レビュー数')
axes[0].set_ylabel('商品数')
save(fig, 'ch03_histogram')


# ============================================================
# 図3.4: カテゴリ別購買数 箱ひげ図
# ============================================================
fig, ax = plt.subplots(figsize=(5.0, 3.2))
cat_order = ['家電', '書籍', 'ファッション', '食品']
data_by_cat = [df[df['category'] == c]['purchases'].values for c in cat_order]
labels_with_n = [f'{c}\n(n={len(d)})' for c, d in zip(cat_order, data_by_cat)]

ax.boxplot(
    data_by_cat,
    tick_labels=labels_with_n,
    widths=0.5,
    patch_artist=True,
    medianprops=dict(color='#222222', linewidth=1.2),
    boxprops=dict(facecolor='#E8EEF4', edgecolor='#4C7CA8', linewidth=0.8),
    whiskerprops=dict(color='#4C7CA8', linewidth=0.8),
    capprops=dict(color='#4C7CA8', linewidth=0.8),
    flierprops=dict(marker='o', markersize=3, markerfacecolor='none',
                    markeredgecolor='#4C7CA8', markeredgewidth=0.6),
)
ax.set_ylabel('購買数')
ax.set_xlabel('')
ax.grid(axis='y', alpha=0.7)
save(fig, 'ch03_boxplot')


# ============================================================
# 図3.5: レビュー数 × 購買数 散布図 (星評価で離散色分け)
# ============================================================
fig, ax = plt.subplots(figsize=(5.2, 3.4))

# 星評価を順序データとして同色相の濃淡で表す
cmap = LinearSegmentedColormap.from_list(
    'stars', ['#D6E3F0', '#7DA8CC', '#1F4F7A']
)
star_levels = sorted(df['stars'].unique())
n_levels = len(star_levels)
discrete_colors = [cmap(i / (n_levels - 1)) for i in range(n_levels)]

for s, col in zip(star_levels, discrete_colors):
    mask = df['stars'] == s
    ax.scatter(
        df.loc[mask, 'reviews'], df.loc[mask, 'purchases'],
        s=28, color=col, edgecolor='white', linewidth=0.5,
        label=f'{s:.1f}',
    )

ax.legend(
    title='星評価', loc='lower right',
    fontsize=7, title_fontsize=8,
    handletextpad=0.3, labelspacing=0.3,
)

ax.set_xlabel('レビュー数')
ax.set_ylabel('購買数')
ax.grid(axis='both', alpha=0.7)
save(fig, 'ch03_scatter')

print('all done')
