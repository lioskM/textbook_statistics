# 統計学教科書

文系大学生・社会人向けの統計学教科書。確率パートの後続文書として位置づけられる。

## ディレクトリ構成

```
textbook_statistics/
├── .gitignore
├── README.md
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
├── docs/                              # 設計文書
│   ├── 要件定義書.txt
│   ├── 統計学教科書_章構成案.md
│   └── リズム原則.md
├── references/                        # 参考資料（エージェントは参照しない）
└── review/                            # 執筆パイプライン
    ├── latex_reference.md             # LaTeX環境名・章ファイル対応表
    ├── review.ps1                     # 実行スクリプト
    └── agents/                        # エージェントプロンプト
        ├── 00_educational_design.md
        ├── 01_text_generation.md
        ├── 03_statistical_accuracy.md
        ├── 04_structural_consistency.md
        ├── 05_writing_quality.md
        ├── role_a_reader.md
        └── role_b_writer.md
```

## バージョン管理方針

- ファイル名にバージョン番号を含めない
- バージョン管理は Git に集約する
- 各設計文書（要件定義書、章構成案）の冒頭ヘッダおよび変更履歴セクションで現バージョンを示す
- 過去版を参照したい場合は `git log` および `git show` を使う

## 執筆パイプライン

教科書の各章は、以下の段階を経て執筆される。

```
章構成案 + 前章LaTeX
  │
  ▼
① 教育設計（agents/00_educational_design.md）
  │  読者の認知動線、概念の必然性チェーン、驚きポイント、具体例候補を設計
  ▼
② 本文生成（agents/01_text_generation.md）
  │  教育設計ドキュメントを入力としてLaTeX本文を生成
  ▼
③ Role A/B ループ（agents/role_a_reader.md ↔ agents/role_b_writer.md）
  │  Role A: 読者視点で退屈・混乱・未回答の疑問を報告
  │  Role B: 報告を受けて段落単位で書き直し
  │  必要に応じて複数回のループを実行
  ▼
④ 統計的正確性（agents/03_statistical_accuracy.md）
  │  定義・数式・前提条件の誤り、用語の表記ゆれを検出・修正
  ▼
⑤ 構造・整合性（agents/04_structural_consistency.md）
  │  概念導入順序、章構成案との整合、6ステップ充足を検出・修正
  ▼
⑥ 文章品質（agents/05_writing_quality.md）
  │  禁止語、アンチパターン、教科書固有基準の最終チェック
  ▼
最終稿
```

### 順序の根拠

- ①が最初：教育設計なしに本文を書くと、読者の疑問が想定されないまま手法説明だけが並ぶ
- ②が次：設計に基づいて本文を生成
- ③で読者視点：機械的な品質チェックの前に、読者として読んで面白いか・わかるかを優先
- ④以降は順序が重要：統計的に間違っている文を磨いても無駄、構造的に不要な段落の削除や順序入れ替えが後段の文体修正を無駄にするのを防ぐ、文章品質は最後

### Role A/B ループについて

従来の単一段階のリズム・執筆エージェント（旧02段）を、Role A（読者視点）と Role B（執筆者）の対話ループに置き換えた。読者の具体的なフィードバックを受けて書き直すことで、より読者に届く文章になる。8章で実験的に試した際、構造的に最も完成度の高い結果が得られたため、本パイプラインに正式採用した。

## 章タイプ別の扱い

### 6ステップ適用章
2〜5章, 6章Part A, 7章, 8章は、標準的な6ステップ構成（問い→素朴な方法と限界→理論の最小核→手法→実践→結果と次の一手）に沿って執筆する。

### 6ステップ例外章
以下の章は6ステップ不適用。章構成案で独自構成が指定されている。

- **1章（overview）**：本書全体の見取り図。要件§4.4〜§4.6の記述ルールも外す。
- **6章Part B（Part Aの数学的補遺）**：t統計量・自由度・Welch検定・カイ二乗検定の数学的根拠と数値計算。
- **9章（手法の外側を知る）**：本書全体の総括。バイアスと誤用を既習章の手法と対応づける。

## 各エージェントの参照ファイル

| エージェント | 必須参照 | 任意参照 |
|---|---|---|
| ① 教育設計 | docs/要件定義書.txt §5.2, §6 / docs/統計学教科書_章構成案.md | 前章のLaTeX |
| ② 本文生成 | docs/要件定義書.txt（全体） / docs/統計学教科書_章構成案.md / review/latex_reference.md | — |
| ③ Role A | （特になし） | docs/統計学教科書_章構成案.md |
| ③ Role B | docs/リズム原則.md / docs/要件定義書.txt §3, §4.4, §4.5, §5.2 | — |
| ④ 統計的正確性 | docs/要件定義書.txt §4.4, §4.8, §6 / review/latex_reference.md | 対象章のLaTeX |
| ⑤ 構造・整合性 | docs/要件定義書.txt §5.2, §6, §4.9 / docs/統計学教科書_章構成案.md / review/latex_reference.md | 前章までのLaTeX |
| ⑥ 文章品質 | docs/要件定義書.txt §3, §4.4, §4.5, §4.6 | — |

## 実行方法

各エージェントを `claude --print --model opus` で順次実行し、前段の出力を次段の入力として渡す。

PowerShell環境では UTF-8 エンコーディングを明示的に設定する：

```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

参照ファイルは `--add-dir` オプションで提供する（例：`--add-dir docs --add-dir chapters`）。エージェントプロンプト内ではファイル名のみで参照しているため、必要なディレクトリを渡してパス解決はClaude Code側に任せる。

## 出力フォーマット

各エージェントは以下を出力する：

- **教育設計（00）**：マークダウン形式の設計ドキュメント
- **その他のエージェント**：LaTeX全文
  - 変更一覧・説明文・コメントは含めない
  - コードフェンスで囲まない
  - LaTeXソースをそのまま、先頭の `\section` から末尾まで出力する

## ビルド

```
cd chapters
platex main.tex
platex main.tex
dvipdfmx main.dvi
```

ビルド成果物（`*.aux`, `*.log`, `*.out`, `*.toc`, `*.dvi`, `*.pdf` 等）は `.gitignore` で除外されている。
