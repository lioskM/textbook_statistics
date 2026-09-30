"""第二稿 第2章 図生成スクリプト

生成される図:
  - ch02_ab.pdf        : 商品AとBのレビュー20件を点数ごとに数えた棒グラフ (軸をそろえた2枚. 本文ではヒストグラムと呼ばない)
  - ch02_views.pdf     : 邦画80本の公開後30日間の視聴回数のヒストグラム
  - ch02_col_width.pdf : 同じデータを階級の幅を変えて描いた2枚 (細かい幅では山が二つ, 粗い幅では一つ)
  - ch02_col_box.pdf   : 山が一つのデータと山が二つのデータ (上: ヒストグラム, 下: 箱ひげ図. 五つの数が一致)
  - ch02_col_axis.pdf  : 同じ散布図を軸の縦横比だけ変えて並べた2枚

コラムの図のデータ (col_width, col_box) は本書のために作った架空のもの.

実行:
  uv run python figures/scripts/ch02.py
出力:
  figures/output/ch02_*.pdf, ch02_*.png
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


def save(fig, name: str) -> None:
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png')
    plt.close(fig)
    print(f'saved: {name}')


# ============================================================
# 図: 商品AとB (本文の数値どおり. A: 3点5件・4点10件・5点5件, B: 1点5件・5点15件)
# ============================================================
scores = np.arange(1, 6)
count_a = np.array([0, 0, 5, 10, 5])
count_b = np.array([5, 0, 0, 0, 15])
assert count_a.sum() == 20 and count_b.sum() == 20
assert (scores * count_a).sum() / 20 == 4.0 and (scores * count_b).sum() / 20 == 4.0

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
for ax, cnt, name in zip(axes, [count_a, count_b], ['商品A', '商品B']):
    ax.bar(scores, cnt, color=BLUE, width=0.8)
    ax.set_title(name)
    ax.set_xlabel('星の数')
    ax.set_xticks(scores)
    ax.set_ylim(0, 16)
axes[0].set_ylabel('件数')
fig.tight_layout()
save(fig, 'ch02_ab')


# ============================================================
# 図: 邦画80本の視聴回数のヒストグラム
# ============================================================
df = load_movies()
views_man = df['views_30d'] / 1e4
budget_oku = df['budget'] / 1e8

fig, ax = plt.subplots(figsize=(6.0, 2.8))
ax.hist(views_man, bins=12, color=BLUE, edgecolor='white', linewidth=0.5)
# 本文が図の上の位置を語るので, 平均 (破線) と中央値 (点線) の位置を縦線で示す
ax.axvline(views_man.mean(), color='black', linestyle='--', linewidth=1.0, label='平均')
ax.axvline(views_man.median(), color='black', linestyle=':', linewidth=1.2, label='中央値')
ax.legend(frameon=False)
ax.set_xlabel('視聴回数 (万回)')
ax.set_ylabel('作品数')
fig.tight_layout()
save(fig, 'ch02_views')


# ============================================================
# コラムの図: 階級の幅で山の数が変わる (架空データ)
# ============================================================
rng = np.random.default_rng(20260922)
width_data = np.concatenate([rng.normal(40, 5, 120), rng.normal(62, 5, 120)])

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
axes[0].hist(width_data, bins=np.arange(20, 85, 2), color=BLUE, edgecolor='white', linewidth=0.5)
axes[0].set_title('幅を細かく取る')
axes[1].hist(width_data, bins=np.arange(20, 100, 20), color=BLUE, edgecolor='white', linewidth=0.5)
axes[1].set_title('幅を粗く取る')
for ax in axes:
    ax.set_xlabel('点数')
    ax.set_ylabel('件数')
fig.tight_layout()
save(fig, 'ch02_col_width')

# 粗い幅で山が一つになっていることを数で確かめる
coarse, _ = np.histogram(width_data, bins=np.arange(20, 100, 20))
fine, _ = np.histogram(width_data, bins=np.arange(20, 85, 2))
peaks_fine = sum(1 for i in range(1, len(fine) - 1) if fine[i] > fine[i - 1] and fine[i] >= fine[i + 1] and fine[i] > 10)
print('col_width: 粗い幅の度数', coarse.tolist(), '/ 細かい幅の主な山の数', peaks_fine)


# ============================================================
# コラムの図: 山が二つでも箱ひげ図は同じ (架空データ. 五つの数を一致させる)
# ============================================================
# 山が二つ: 30 と 70 のまわりの二つの山に, 両端へ少数の裾を足す (裾があるので最小値・最大値が山から離れる)
bimodal = np.sort(np.concatenate([rng.normal(30, 5, 276), rng.normal(70, 5, 276),
                                  rng.uniform(5, 18, 24), rng.uniform(82, 95, 24)]))
five = np.percentile(bimodal, [0, 25, 50, 75, 100])
# 山が一つ: 中心 50 の幅広い釣鐘型 (裾を [5, 95] に収める). 五つの数が bimodal と一致するように,
# 五つの点だけで区分線形に写す. もとの形が近いので写しは緩く, 山は一つのまま残る.
pool = rng.normal(50, 32, 400000)
pool = pool[(pool > 5) & (pool < 95)]
# 乱数の凹凸を持ち込まないよう, 裾を切った釣鐘型の分位点を等間隔に 600 個取る (滑らかな山が一つ)
base = np.percentile(pool, (np.arange(600) + 0.5) / 600 * 100)
base_five = np.percentile(base, [0, 25, 50, 75, 100])
unimodal = np.interp(base, base_five, five)
uni_five = np.percentile(unimodal, [0, 25, 50, 75, 100])
assert np.allclose(uni_five, five, atol=0.5), (uni_five, five)
print('col_box: 五つの数 (最小, Q1, 中央値, Q3, 最大) 山一つ', np.round(uni_five, 1).tolist(), '/ 山二つ', np.round(five, 1).tolist())

fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.4), sharex=True,
                         gridspec_kw={'height_ratios': [3, 1]})
bins = np.arange(0, 101, 5)
for j, (data, name) in enumerate([(unimodal, '山が一つ'), (bimodal, '山が二つ')]):
    axes[0, j].hist(data, bins=bins, color=BLUE, edgecolor='white', linewidth=0.5)
    axes[0, j].set_title(name)
    axes[0, j].set_ylabel('件数')
    axes[1, j].boxplot(data, vert=False, whis=(0, 100), widths=0.5,
                       medianprops={'color': 'black'})
    axes[1, j].set_yticks([])
    axes[1, j].set_xlabel('点数')
fig.tight_layout()
save(fig, 'ch02_col_box')


# ============================================================
# コラムの図: 軸の縦横比で傾きが変わる (80本の製作費と視聴回数)
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), gridspec_kw={'width_ratios': [1, 2.2]})
for ax in axes:
    ax.scatter(budget_oku, views_man, s=12, color=BLUE, alpha=0.8)
    ax.set_xlabel('製作費 (億円)')
    ax.set_ylabel('視聴回数 (万回)')
axes[0].set_box_aspect(2.2)
axes[0].set_title('縦軸を引き伸ばす')
axes[1].set_box_aspect(0.35)
axes[1].set_title('横軸を引き伸ばす')
fig.tight_layout()
save(fig, 'ch02_col_axis')
