"""第5章 図生成スクリプト

生成される図:
  - ch05_ci_coverage.pdf : 95%信頼区間を100回作るシミュレーション

実行:
  uv run python figures/scripts/ch05.py
出力:
  figures/output/ch05_*.pdf, ch05_*.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
OUTDIR = SCRIPT_DIR.parent / 'output'
OUTDIR.mkdir(exist_ok=True)

plt.style.use(str(SCRIPT_DIR / 'textbook.mplstyle'))


def save(fig, name: str) -> None:
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png')
    plt.close(fig)
    print(f'saved: {name}')


# ============================================================
# 図5.1: 95%信頼区間のシミュレーション (100回の取り直し)
#   母平均4.1, 母標準偏差0.7 の仕組みから n=50 の標本を取り,
#   平均 ± 2SE の区間を作る手順を100回繰り返す (seed=42).
#   本文は「93本が含み, 7本が外した」と記述しており,
#   seed を変える場合は本文の記述も合わせて更新すること.
# ============================================================
rng = np.random.default_rng(42)
MU, SIGMA, N, REPS = 4.1, 0.7, 50, 100

intervals = []
for _ in range(REPS):
    x = rng.normal(MU, SIGMA, N)
    m = x.mean()
    se = x.std(ddof=1) / np.sqrt(N)
    intervals.append((m - 2 * se, m + 2 * se))

fig, ax = plt.subplots(figsize=(5.2, 5.4))
n_miss = 0
for i, (lo, hi) in enumerate(intervals, start=1):
    contains = lo <= MU <= hi
    if not contains:
        n_miss += 1
    color = '#4C7CA8' if contains else '#D55E00'
    lw = 0.9 if contains else 1.6
    ax.hlines(y=i, xmin=lo, xmax=hi, color=color, linewidth=lw)
ax.axvline(MU, color='#333333', linestyle='--', linewidth=1.0)
ax.text(MU, REPS + 3, f'母平均 {MU}', ha='center', va='bottom',
        fontsize=8, color='#333333')
ax.set_xlabel('平均評価')
ax.set_ylabel('何回目の取り直しか')
ax.set_ylim(0, REPS + 8)
ax.grid(False)
fig.tight_layout()
save(fig, 'ch05_ci_coverage')
print(f'misses: {n_miss} / {REPS}')
