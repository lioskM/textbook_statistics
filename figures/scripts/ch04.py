"""第4章 図生成スクリプト.

生成される図:
  - ch04_hist_compare.pdf: 製作費と評価件数のヒストグラム
  - ch04_normal_ranges.pdf: 正規分布の±1σ, ±2σ, ±3σ
  - ch04_dice_clt.pdf: 偏ったサイコロと標本平均の分布
  - ch04_sampling_dist.pdf: 視聴回数と標本平均の分布

実行:
  uv run python figures/scripts/ch04.py
出力:
  figures/output/ch04_*.pdf, ch04_*.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ch03_data import load_movies

SCRIPT_DIR = Path(__file__).resolve().parent
OUTDIR = SCRIPT_DIR.parent / 'output'
OUTDIR.mkdir(exist_ok=True)

plt.style.use(str(SCRIPT_DIR / 'textbook.mplstyle'))

BLUE = '#4C7CA8'
ORANGE = '#D55E00'
SEED = 42


def save(fig, name: str) -> None:
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png')
    plt.close(fig)
    print(f'saved: {name}')


df = load_movies()


# ============================================================
# 図4.1: 製作費と評価件数のヒストグラム
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
axes[0].hist(df['budget'] / 1e8, bins=15, color=BLUE,
             edgecolor='white', linewidth=0.5)
axes[0].set_title('(a) 製作費')
axes[0].set_xlabel('製作費 (億円)')
axes[0].set_ylabel('作品数')

axes[1].hist(df['rating_count'] / 1e4, bins=15, color=BLUE,
             edgecolor='white', linewidth=0.5)
axes[1].set_title('(b) 評価件数')
axes[1].set_xlabel('評価件数 (万件)')
fig.tight_layout()
save(fig, 'ch04_hist_compare')


# ============================================================
# 図4.2: 正規分布の±1σ, ±2σ, ±3σ
# ============================================================
x = np.linspace(-4, 4, 1200)
y = np.exp(-(x ** 2) / 2) / np.sqrt(2 * np.pi)
fig, ax = plt.subplots(figsize=(6.0, 3.2))
ax.plot(x, y, color='#222222', linewidth=1.2)
for limit, color in [(3, '#DDEAF3'), (2, '#A9C9DF'), (1, '#6D9FBE')]:
    mask = np.abs(x) <= limit
    ax.fill_between(x[mask], 0, y[mask], color=color, linewidth=0)
for limit, linestyle in [(1, '-'), (2, '--'), (3, ':')]:
    for sign in (-1, 1):
        ax.axvline(sign * limit, color='#333333', linestyle=linestyle,
                   linewidth=0.8)
ax.axvline(0, color=ORANGE, linewidth=1.0)
ax.text(0, 0.405, r'$\mu$', ha='center', va='bottom', color=ORANGE)
ax.text(0, 0.30, r'$\pm1\sigma$: 約68%', ha='center', va='center')
ax.text(0, 0.22, r'$\pm2\sigma$: 約95%', ha='center', va='center')
ax.text(0, 0.14, r'$\pm3\sigma$: 約99.7%', ha='center', va='center')
ax.set_xticks(range(-3, 4))
ax.set_xticklabels([
    r'$\mu-3\sigma$', r'$\mu-2\sigma$', r'$\mu-\sigma$', r'$\mu$',
    r'$\mu+\sigma$', r'$\mu+2\sigma$', r'$\mu+3\sigma$',
])
ax.set_yticks([])
ax.set_ylabel('確率密度')
ax.set_xlim(-4, 4)
ax.set_ylim(0, 0.43)
ax.grid(False)
fig.tight_layout()
save(fig, 'ch04_normal_ranges')


# ============================================================
# 図4.3: 偏ったサイコロと標本平均の分布
# ============================================================
rng = np.random.default_rng(SEED)
faces = np.arange(1, 7)
probabilities = np.array([0.5, 0.1, 0.1, 0.1, 0.1, 0.1])
means_5 = rng.choice(faces, size=(1000, 5), p=probabilities).mean(axis=1)
means_30 = rng.choice(faces, size=(1000, 30), p=probabilities).mean(axis=1)

fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.7), sharex=True)
axes[0].bar(faces, probabilities, color=BLUE, edgecolor='white', linewidth=0.5)
axes[0].set_title('(a) 1回の出目')
axes[0].set_ylabel('確率')
axes[0].set_ylim(0, 0.55)

bins_5 = np.arange(0.9, 6.11, 0.2)
bins_30 = np.arange(0.95, 6.06, 0.10)
assert np.allclose(np.diff(bins_5), 1 / 5)
assert np.allclose((bins_5[:-1] + bins_5[1:]) / 2,
                   np.arange(5, 31) / 5)
assert np.allclose(means_5 * 5, np.round(means_5 * 5))
for ax, means, panel_bins, rwidth, label in [
    (axes[1], means_5, bins_5, 0.72, '(b) 5回の平均'),
    (axes[2], means_30, bins_30, 1.0, '(c) 30回の平均'),
]:
    ax.hist(means, bins=panel_bins,
            weights=np.full(len(means), 1 / len(means)), rwidth=rwidth,
            color=BLUE, edgecolor='white', linewidth=0.35)
    ax.axvline(2.5, color=ORANGE, linestyle='--', linewidth=1.0)
    ax.set_title(label)
    ax.set_xlabel('値')
    ax.set_ylabel('割合')
    ax.set_xlim(0.8, 6.2)
    ax.set_xticks(faces)
fig.tight_layout()
save(fig, 'ch04_dice_clt')


# ============================================================
# 図4.4: 視聴回数と復元抽出した標本平均の分布
# ============================================================
rng = np.random.default_rng(SEED)
views = df['views_30d'].to_numpy(dtype=float) / 1e4
means = rng.choice(views, size=(1000, 20), replace=True).mean(axis=1)
bins = np.linspace(0, views.max() * 1.02, 51)
empirical_mean = views.mean()

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharex=True, sharey=True)
for ax, values, label in [
    (axes[0], views, '(a) 元の80本'),
    (axes[1], means, '(b) 20本の平均を1000回'),
]:
    ax.hist(values, bins=bins, weights=np.full(len(values), 1 / len(values)),
            color=BLUE, edgecolor='white', linewidth=0.5)
    ax.axvline(empirical_mean, color=ORANGE, linestyle='--', linewidth=1.0)
    ax.set_title(label)
    ax.set_xlabel('視聴回数 (万回)')
axes[0].set_ylabel('割合')
fig.tight_layout()
save(fig, 'ch04_sampling_dist')

print('all done')
