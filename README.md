# 統計学教科書

文系大学生・社会人向けの統計学教科書。確率パートの後続文書として位置づけられる。

## ディレクトリ構成

```
textbook_statistics/
├── .gitignore
├── README.md
├── CLAUDE.md
├── chapters/                          # 教科書本体
│   ├── main.tex                       # ルートファイル（コンパイル対象）
│   ├── pre.sty                        # スタイル定義
│   ├── intro_statistics.tex           # 1章
│   ├── data_summarization.tex         # 2章
│   ├── data_visualization.tex         # 3章
│   ├── probability_distribution.tex   # 4章
│   ├── inference.tex                  # 5章
│   ├── statistical_test.tex           # 6章 Part A
│   ├── statistical_test_precise.tex   # 6章 Part B
│   ├── correlations.tex               # 7章
│   ├── regression.tex                 # 8章
│   └── limitations_and_ethics.tex     # 9章（執筆予定）
├── docs/                              # 設計・実務文書
│   ├── 要件定義書.md
│   ├── リズム原則.md
│   ├── 概念導入順序整理.md            # 各章の概念初出順の追認表
│   ├── latex_reference.md             # LaTeX環境名・章ファイル対応表
│   ├── データ設計ドキュメント.md      # データを扱う章の任意参照
│   ├── ランニング例設定メモ_v2.md
│   └── 統計学教科書_章構成案.md
├── figures/                           # 図の生成
│   ├── scripts/                       # 章別の図生成スクリプト
│   │   ├── ch03.py
│   │   ├── ch03_data.py
│   │   ├── ch05.py
│   │   └── textbook.mplstyle          # matplotlib 共通スタイル
│   └── output/                        # 生成された図（PDF/PNG）
├── data/                              # 本文で用いるデータ
│   └── running_example.csv            # ランニング例データ
├── references/                        # 参考資料（参照しない）
└── review/                            # （凍結・参照外）旧・自動レビューパイプライン
```

## バージョン管理方針

- ファイル名にバージョン番号を含めない
- バージョン管理は Git に集約する
- 各設計文書（要件定義書、章構成案）の冒頭ヘッダおよび変更履歴セクションで現バージョンを示す
- 過去版を参照したい場合は `git log` および `git show` を使う

## 執筆・校正の進め方

本書の各章は、章ごとに個別の作成指示書に基づいて執筆・校正する。独立したエディトリアルレビューが必要な場合は、外部モデル（GPT または Gemini）に出す。

かつての自動レビューパイプライン（`review/` 配下のエージェント群）は凍結済みで、現在は参照しない。過去の設計知見の記録としてディレクトリは残すが、実運用の対象外とする。

## 章タイプ別の扱い

### 6ステップ適用章
2〜5章, 6章Part A, 7章, 8章は、標準的な6ステップ構成（問い→素朴な方法と限界→理論の最小核→手法→実践→結果と次の一手）に沿って執筆する。

### 6ステップ例外章
以下の章は6ステップ不適用。章構成案で独自構成が指定されている。

- **1章（overview）**：本書全体の見取り図。要件§4.4〜§4.6の記述ルールも外す。
- **6章Part B（Part Aの数学的補遺）**：t統計量・自由度・Welch検定・カイ二乗検定の数学的根拠と数値計算。
- **9章（手法の外側を知る）**：本書全体の総括。バイアスと誤用を既習章の手法と対応づける。

## ビルド

```
cd chapters
platex main.tex
platex main.tex
dvipdfmx main.dvi
```

ビルド成果物（`*.aux`, `*.log`, `*.out`, `*.toc`, `*.dvi`, `*.pdf` 等）は `.gitignore` で除外されている。
