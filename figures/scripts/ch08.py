"""第8章 図生成スクリプト.

生成される図:
  - ch08_actual_scatter.pdf: 製作費／おすすめ表示回数と視聴回数
  - ch08_correlation_examples.pdf: 相関係数の代表値
  - ch08_actual_correlations.pdf: 実データの三つの相関
  - ch08_outlier.pdf: 外れ値による相関の変化
  - ch08_simpson.pdf: シンプソンのパラドックス

実行:
  uv run python figures/scripts/ch08.py
出力:
  figures/output/ch08_*.pdf, ch08_*.png
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
GREEN = '#009E73'
GRAY = '#555555'


def save(fig, name: str) -> None:
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png')
    plt.close(fig)
    print(f'saved: {name}')


def exact_correlation_points(r: float, n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """標本相関係数が数値誤差の範囲でrとなる合成点を返す."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    x = (x - x.mean()) / x.std(ddof=1)
    if abs(r) == 1:
        return x, np.sign(r) * x
    z = rng.normal(size=n)
    z -= z.mean()
    z -= np.dot(z, x) / np.dot(x, x) * x
    z /= z.std(ddof=1)
    y = r * x + np.sqrt(1 - r ** 2) * z
    return x, y


df = load_movies()
views_man = df['views_30d'] / 1e4
budget_oku = df['budget'] / 1e8
recommend_man = df['rec_impressions'] / 1e4


# ============================================================
# 図8.1: 実データの散布図2枚
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
for ax, x, xlabel, label in [
    (axes[0], budget_oku, '製作費 (億円)', '(a) 製作費'),
    (axes[1], recommend_man, 'おすすめ表示回数 (万回)', '(b) おすすめ表示回数'),
]:
    ax.scatter(x, views_man, s=22, color=BLUE, edgecolor='white',
               linewidth=0.4, alpha=0.9)
    ax.set_title(label)
    ax.set_xlabel(xlabel)
    ax.grid(axis='both', alpha=0.7)
axes[0].set_ylabel('視聴回数 (万回)')
fig.tight_layout()
save(fig, 'ch08_actual_scatter')


# ============================================================
# 図8.2: 相関係数の代表値
# ============================================================
correlation_values = [-1.0, -0.7, 0.0, 0.3, 0.8, 1.0]
fig, axes = plt.subplots(1, 6, figsize=(7.5, 1.9), sharex=True, sharey=True)
for i, (ax, r) in enumerate(zip(axes, correlation_values)):
    x, y = exact_correlation_points(r, n=60, seed=810 + i)
    measured = np.corrcoef(x, y)[0, 1]
    assert np.isclose(measured, r, atol=1e-12)
    ax.scatter(x, y, s=10, color=BLUE, edgecolor='none', alpha=0.8)
    ax.set_title(f'$r={r:g}$')
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
fig.tight_layout(w_pad=0.6)
save(fig, 'ch08_correlation_examples')


# ============================================================
# 図8.3: 実データの三つの相関係数
# ============================================================
actual_pairs = [
    ('製作費', df['budget'].corr(df['views_30d'])),
    ('おすすめ表示回数', df['rec_impressions'].corr(df['views_30d'])),
    ('平均評価', df['avg_rating'].corr(df['views_30d'])),
]
expected = [0.364959, 0.803335, 0.205664]
assert np.allclose([value for _, value in actual_pairs], expected, atol=5e-7)

fig, ax = plt.subplots(figsize=(5.4, 2.8))
labels = [label for label, _ in actual_pairs]
values = [value for _, value in actual_pairs]
ypos = np.arange(len(labels))
bars = ax.barh(ypos, values, color=[BLUE, ORANGE, GREEN], height=0.55,
               edgecolor='#333333', linewidth=0.4)
for bar, value in zip(bars, values):
    ax.text(value + 0.025, bar.get_y() + bar.get_height() / 2,
            f'{value:.4f}', va='center', ha='left')
ax.axvline(0, color='#333333', linewidth=0.8)
ax.set_yticks(ypos, labels=labels)
ax.invert_yaxis()
ax.set_xlim(-1, 1)
ax.set_xlabel('視聴回数との相関係数 $r$')
ax.grid(axis='x', alpha=0.7)
fig.tight_layout()
save(fig, 'ch08_actual_correlations')


# ============================================================
# 図8.4: 外れ値による相関の変化
# ============================================================
x_base = np.arange(1, 11)
y_base = np.array([6, 1, 7, 5, 8, 3, 10, 9, 2, 4])
x_added = np.append(x_base, 22)
y_added = np.append(y_base, 22)
r_base = np.corrcoef(x_base, y_base)[0, 1]
r_added = np.corrcoef(x_added, y_added)[0, 1]
assert np.isclose(r_base, 0.0545454545)
assert np.isclose(r_added, 0.7636363636)

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
axes[0].scatter(x_base, y_base, s=28, color=BLUE, edgecolor='white',
                linewidth=0.4)
axes[0].set_title(f'(a) 10点: $r={r_base:.2f}$')
axes[0].set_xlim(0, 11)
axes[0].set_ylim(0, 11)

axes[1].scatter(x_base, y_base, s=28, color=BLUE, edgecolor='white',
                linewidth=0.4, label='元の10点')
axes[1].scatter([22], [22], s=48, marker='X', color=ORANGE,
                edgecolor='#333333', linewidth=0.5, label='追加した1点')
axes[1].set_title(f'(b) 1点追加: $r={r_added:.2f}$')
axes[1].set_xlim(0, 24)
axes[1].set_ylim(0, 24)
axes[1].legend(loc='upper left')
for ax in axes:
    ax.set_xlabel('$X$')
    ax.set_ylabel('$Y$')
    ax.grid(axis='both', alpha=0.7)
fig.tight_layout()
save(fig, 'ch08_outlier')


# ============================================================
# 図8.5: シンプソンのパラドックス
# ============================================================
x_a_std, y_a_std = exact_correlation_points(0.7, n=30, seed=820)
x_b_std, y_b_std = exact_correlation_points(0.6, n=30, seed=821)
x_a = 3 + x_a_std
y_a = 76 + 8 * y_a_std
x_b = 7 + x_b_std
y_b = 64 + 8 * y_b_std
x_all = np.concatenate([x_a, x_b])
y_all = np.concatenate([y_a, y_b])
r_a = np.corrcoef(x_a, y_a)[0, 1]
r_b = np.corrcoef(x_b, y_b)[0, 1]
r_all = np.corrcoef(x_all, y_all)[0, 1]
assert np.isclose(r_a, 0.7)
assert np.isclose(r_b, 0.6)
assert -0.34 < r_all < -0.28

fig, ax = plt.subplots(figsize=(5.6, 3.4))
ax.scatter(x_a, y_a, s=26, marker='o', facecolor='none', edgecolor=BLUE,
           linewidth=0.8, label=f'学部A ($r={r_a:.1f}$)')
ax.scatter(x_b, y_b, s=28, marker='^', facecolor='none', edgecolor=ORANGE,
           linewidth=0.9, label=f'学部B ($r={r_b:.1f}$)')
for x, y, color, linestyle in [
    (x_a, y_a, BLUE, '-'),
    (x_b, y_b, ORANGE, '--'),
]:
    slope, intercept = np.polyfit(x, y, 1)
    line_x = np.linspace(x.min(), x.max(), 100)
    ax.plot(line_x, intercept + slope * line_x, color=color,
            linestyle=linestyle, linewidth=1.1)
all_slope, all_intercept = np.polyfit(x_all, y_all, 1)
line_x = np.linspace(x_all.min(), x_all.max(), 100)
ax.plot(line_x, all_intercept + all_slope * line_x, color=GRAY,
        linestyle=':', linewidth=1.4, label=f'全体 ($r={r_all:.2f}$)')
ax.set_xlabel('勉強時間 (時間)')
ax.set_ylabel('試験得点')
ax.grid(axis='both', alpha=0.7)
ax.legend()
fig.tight_layout()
save(fig, 'ch08_simpson')

print(f'actual correlations: {values}')
print(f'outlier example: {r_base:.6f} -> {r_added:.6f}')
print(f'Simpson example: A={r_a:.6f}, B={r_b:.6f}, all={r_all:.6f}')
print('all done')
