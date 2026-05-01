# textbook_statistics

文系大学生・社会人向けの統計学教科書 (LaTeX).

## 必読 (タスク種別による)

- 構造把握: `README.md`
- 校正・執筆: `review/agents/` の該当ファイル + `docs/リズム原則.md` + `docs/要件定義書.txt`
- LaTeX 環境名・コマンド: `review/latex_reference.md`

## コマンド

- LaTeX 組版: `platex main.tex && dvipdfmx main.dvi`
- 図生成: `figures/scripts/` 内の章別スクリプトを `uv run python` で実行
  (例: `uv run python figures/scripts/ch03.py`)

## 絶対ルール

- `references/` は読まない (参考資料、エージェント参照外)
- 統計的主張の意味は変えない
