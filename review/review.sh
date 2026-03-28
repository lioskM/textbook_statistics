#!/bin/bash
# 統計学教科書 レビューパイプライン
# 使い方: ./review.sh <章LaTeXファイル>
# 例:     ./review.sh chapters/probability_distribution.tex

set -euo pipefail

INPUT="$1"
BASENAME=$(basename "$INPUT" .tex)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="${BASENAME}_reviewed_${TIMESTAMP}.tex"

DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS="$DIR/agents"
DOCS="$DIR/../docs"
LATEX_REF="$DIR/latex_reference.md"

# 参照ファイル読み込み
REQ=$(cat "$DOCS/要件定義書_v3_0.txt")
CHAP=$(cat "$DOCS/統計学教科書_章構成案_v3.md")
RHYTHM=$(cat "$DOCS/リズム原則_v1.md")
LATEXREF=$(cat "$LATEX_REF")

echo "=== レビュー開始: $INPUT ==="
echo "出力先: $OUTPUT"
echo ""

echo "[1/4] 統計的正確性..."
AGENT1=$(cat "$AGENTS/01_statistical_accuracy.md")
SYSPROMPT1=$(printf '%s\n\n---\n# 参照: 要件定義書\n%s\n\n---\n# 参照: LaTeXリファレンス\n%s' "$AGENT1" "$REQ" "$LATEXREF")
STEP1=$(cat "$INPUT" | claude --print --system-prompt "$SYSPROMPT1")

echo "[2/4] 構造・整合性..."
AGENT2=$(cat "$AGENTS/02_structural_consistency.md")
SYSPROMPT2=$(printf '%s\n\n---\n# 参照: 要件定義書\n%s\n\n---\n# 参照: 章構成案\n%s\n\n---\n# 参照: LaTeXリファレンス\n%s' "$AGENT2" "$REQ" "$CHAP" "$LATEXREF")
STEP2=$(echo "$STEP1" | claude --print --system-prompt "$SYSPROMPT2")

echo "[3/4] 文章品質..."
AGENT3=$(cat "$AGENTS/03_writing_quality.md")
SYSPROMPT3=$(printf '%s\n\n---\n# 参照: 要件定義書\n%s' "$AGENT3" "$REQ")
STEP3=$(echo "$STEP2" | claude --print --system-prompt "$SYSPROMPT3")

echo "[4/4] リズム・グルーヴ..."
AGENT4=$(cat "$AGENTS/04_rhythm.md")
SYSPROMPT4=$(printf '%s\n\n---\n# 参照: リズム原則\n%s' "$AGENT4" "$RHYTHM")
echo "$STEP3" | claude --print --system-prompt "$SYSPROMPT4" > "$OUTPUT"

echo ""
echo "=== 完了: $OUTPUT ==="
