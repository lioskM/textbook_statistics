# textbook_statistics

文系大学生・社会人向けの統計学教科書 (LaTeX).
思考プロセス（Chain of Thought）から最終出力まで、すべて日本語で一貫して行ってください.

## 必読 (タスク種別による)

- 構造把握: `README.md`
- 校正・執筆: `docs/リズム原則.md` + `docs/要件定義書.md` + `docs/概念導入順序整理.md`
- LaTeX 環境名・コマンド: `docs/latex_reference.md`
- データを扱う章のみ任意参照: `docs/データ設計ドキュメント.md`

## コマンド

- LaTeX 組版:
  ```
  cd chapters
  platex main.tex
  platex main.tex
  dvipdfmx main.dvi
  ```
  (相互参照の解決のため platex は2回実行する)
- 図生成: `figures/scripts/` 内の章別スクリプトを `uv run python` で実行
  (例: `uv run python figures/scripts/ch03.py`)

## 絶対ルール

- `references/` は読まない (参考資料、参照外)
- `review/` は読まない (凍結済みのレガシー・パイプライン)
- 統計的主張の意味は変えない
- 思考プロセス（Chain of Thought）から最終出力まで、すべて日本語で一貫して行う
