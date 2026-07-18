"""第9章 図生成スクリプト.

生成される図:
  - ch09_anscombe.pdf: アンスコムのカルテット
  - ch09_fit_comparison.pdf: 散布図と回帰直線の比較
  - ch09_residuals.pdf: 実データの残差プロット

実行:
  uv run python figures/scripts/ch09.py
出力:
  figures/output/ch09_*.pdf, ch09_*.png
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


def save(fig, name: str) -> None:
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png')
    plt.close(fig)
    print(f'saved: {name}')


# ============================================================
# 図9.1: アンスコムのカルテット
# ============================================================
x_common = np.array([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5], dtype=float)
anscombe = [
    (
        x_common,
        np.array([8.04, 6.95, 7.58, 8.81, 8.33, 9.96,
                  7.24, 4.26, 10.84, 4.82, 5.68]),
    ),
    (
        x_common,
        np.array([9.14, 8.14, 8.74, 8.77, 9.26, 8.10,
                  6.13, 3.10, 9.13, 7.26, 4.74]),
    ),
    (
        x_common,
        np.array([7.46, 6.77, 12.74, 7.11, 7.81, 8.84,
                  6.08, 5.39, 8.15, 6.42, 5.73]),
    ),
    (
        np.array([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], dtype=float),
        np.array([6.58, 5.76, 7.71, 8.84, 8.47, 7.04,
                  5.25, 12.50, 5.56, 7.91, 6.89]),
    ),
]

fig, axes = plt.subplots(2, 2, figsize=(6.4, 5.0), sharex=True, sharey=True)
anscombe_stats = []
for index, (ax, (x, y)) in enumerate(zip(axes.flat, anscombe), start=1):
    slope, intercept = np.polyfit(x, y, 1)
    r = np.corrcoef(x, y)[0, 1]
    r_squared = r ** 2
    anscombe_stats.append((slope, intercept, r, r_squared))
    assert np.isclose(x.mean(), 9.0, atol=0.001)
    assert np.isclose(y.mean(), 7.5, atol=0.002)
    assert np.isclose(slope, 0.5, atol=0.002)
    assert np.isclose(intercept, 3.0, atol=0.02)
    assert np.isclose(r, 0.816, atol=0.002)
    ax.scatter(x, y, s=28, color=BLUE, edgecolor='white', linewidth=0.4)
    line_x = np.linspace(3, 20, 100)
    ax.plot(line_x, intercept + slope * line_x, color=ORANGE,
            linewidth=1.0)
    ax.set_title(f'データ組 {index}')
    ax.set_xlim(3, 20)
    ax.set_ylim(2, 14)
    ax.grid(axis='both', alpha=0.7)
for ax in axes[-1, :]:
    ax.set_xlabel('$x$')
for ax in axes[:, 0]:
    ax.set_ylabel('$y$')
fig.tight_layout()
save(fig, 'ch09_anscombe')


# ============================================================
# 図9.2--9.4: ランニング例の散布図・回帰直線・残差
# ============================================================
df = load_movies()
x = df['budget'].to_numpy(dtype=float) / 1e8
y = df['views_30d'].to_numpy(dtype=float) / 1e4
slope, intercept = np.polyfit(x, y, 1)
fitted = intercept + slope * x
residuals = y - fitted
r = np.corrcoef(x, y)[0, 1]
r_squared = r ** 2
positive = int(np.sum(residuals > 1e-12))
negative = int(np.sum(residuals < -1e-12))
middle_band = (fitted >= 150) & (fitted <= 250)
middle_residual_min = residuals[middle_band].min()
middle_residual_max = residuals[middle_band].max()

assert np.isclose(slope, 49.422, atol=0.0005)
assert np.isclose(intercept, 108.410, atol=0.0005)
assert np.isclose(r, 0.3650, atol=0.00005)
assert np.isclose(r_squared, 0.1332, atol=0.00005)
assert (positive, negative) == (24, 56)
assert np.isclose(middle_residual_min, -165.202, atol=0.0005)
assert np.isclose(middle_residual_max, 945.614, atol=0.0005)

# 散布図と回帰直線を左右で比較
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
for ax, title in zip(axes, ['(a) 線を引く前', '(b) 最小二乗回帰直線']):
    ax.scatter(x, y, s=22, color=BLUE, edgecolor='white',
               linewidth=0.4, alpha=0.9)
    ax.set_title(title)
    ax.set_xlabel('製作費 (億円)')
    ax.set_xlim(0, 12)
    ax.grid(axis='both', alpha=0.7)
axes[0].set_ylabel('視聴回数 (万回)')
line_x = np.linspace(x.min(), x.max(), 200)
axes[1].plot(line_x, intercept + slope * line_x, color=ORANGE,
             linewidth=1.3, label=r'$\hat{y}=108.4+49.4x$')
axes[1].legend(loc='upper left')
fig.tight_layout()
save(fig, 'ch09_fit_comparison')

# 残差プロット
fig, ax = plt.subplots(figsize=(5.4, 3.3))
ax.scatter(fitted, residuals, s=24, color=BLUE, edgecolor='white',
           linewidth=0.4, alpha=0.9)
ax.axhline(0, color=ORANGE, linestyle='--', linewidth=1.1)
ax.set_xlabel('予測視聴回数 (万回)')
ax.set_ylabel('残差 (万回)')
ax.grid(axis='both', alpha=0.7)
ax.text(0.98, 0.96, f'正: {positive}本 / 負: {negative}本',
        transform=ax.transAxes, ha='right', va='top')
fig.tight_layout()
save(fig, 'ch09_residuals')

print('Anscombe statistics:')
for index, (slope_i, intercept_i, r_i, r2_i) in enumerate(anscombe_stats, start=1):
    print(
        f'  {index}: slope={slope_i:.4f}, intercept={intercept_i:.4f}, '
        f'r={r_i:.4f}, R2={r2_i:.4f}'
    )
print(
    f'running regression: slope={slope:.6f}, intercept={intercept:.6f}, '
    f'r={r:.6f}, R2={r_squared:.6f}, residual signs={positive}/{negative}'
)
print(
    f'residual range for fitted 150--250: '
    f'{middle_residual_min:.6f}--{middle_residual_max:.6f}'
)
print('all done')
