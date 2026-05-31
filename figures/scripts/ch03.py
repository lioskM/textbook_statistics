"""第3章 図生成スクリプト

生成される図:
  - ch03_histogram.pdf : 視聴回数のヒストグラム (ビン幅3パターン)
  - ch03_boxplot.pdf   : ジャンル別視聴回数の箱ひげ図
  - ch03_scatter.pdf   : 製作費 × 視聴回数の散布図

実行:
  uv run python figures/scripts/ch03.py
出力:
  figures/output/ch03_*.pdf, ch03_*.png
"""
from pathlib import Path

import matplotlib.pyplot as plt

from ch03_data import load_movies

SCRIPT_DIR = Path(__file__).resolve().parent
OUTDIR = SCRIPT_DIR.parent / 'output'
OUTDIR.mkdir(exist_ok=True)

plt.style.use(str(SCRIPT_DIR / 'textbook.mplstyle'))


def save(fig, name: str) -> None:
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png')
    plt.close(fig)
    print(f'saved: {name}')


df = load_movies()
# 視聴回数を万回単位に換算 (図の可読性のため)
views_man = df['views_30d'] / 1e4
# 製作費を億円単位に換算
budget_oku = df['budget'] / 1e8


# ============================================================
# 図3.1: 視聴回数ヒストグラム (ビン幅3パターン)
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=False)
bin_specs = [(5, 'ビン幅 大 (5区間)'),
             (12, 'ビン幅 中 (12区間)'),
             (25, 'ビン幅 小 (25区間)')]
for ax, (n_bins, label) in zip(axes, bin_specs):
    ax.hist(views_man, bins=n_bins, color='#4C7CA8',
            edgecolor='white', linewidth=0.5)
    ax.set_title(label)
    ax.set_xlabel('視聴回数 (万回)')
axes[0].set_ylabel('作品数')
fig.tight_layout()
save(fig, 'ch03_histogram')


# ============================================================
# 図3.2: ジャンル別視聴回数 箱ひげ図
# ============================================================
fig, ax = plt.subplots(figsize=(5.6, 3.2))
genre_order = ['ヒューマンドラマ', 'サスペンス', 'コメディ', '恋愛', 'アクション']
data_by_genre = [views_man[df['genre'] == g].values for g in genre_order]
labels_with_n = [f'{g}\n(n={len(d)})' for g, d in zip(genre_order, data_by_genre)]

ax.boxplot(
    data_by_genre,
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
ax.set_ylabel('視聴回数 (万回)')
ax.set_xlabel('')
ax.grid(axis='y', alpha=0.7)
fig.tight_layout()
save(fig, 'ch03_boxplot')


# ============================================================
# 図3.3: 製作費 × 視聴回数 散布図
# ============================================================
fig, ax = plt.subplots(figsize=(5.2, 3.4))
ax.scatter(
    budget_oku, views_man,
    s=24, color='#4C7CA8', edgecolor='white', linewidth=0.4, alpha=0.9,
)
ax.set_xlabel('製作費 (億円)')
ax.set_ylabel('視聴回数 (万回)')
ax.grid(axis='both', alpha=0.7)
fig.tight_layout()
save(fig, 'ch03_scatter')

print('all done')
