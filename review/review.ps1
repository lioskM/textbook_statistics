# Textbook Review Pipeline (6-stage)
# Usage: powershell -ExecutionPolicy Bypass -File .\review\review.ps1 chapters\probability_distribution.tex
#
# Stages:
#   00 Educational Design  - produce question map, necessity chain, surprise points, examples
#   01 Text Generation     - generate LaTeX draft from design document
#   02 Rhythm & Writing    - rewrite with full authority for quality prose
#   03 Statistical Check   - verify statistical accuracy
#   04 Structural Check    - verify 6-step structure and cross-chapter consistency
#   05 Writing Quality     - final defense: prohibited words, anti-patterns

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not $args[0]) {
    Write-Error "Usage: .\review.ps1 <chapter .tex file>"
    exit 1
}

$INPUT = $args[0]
if (-not (Test-Path $INPUT)) {
    Write-Error "File not found: $INPUT"
    exit 1
}

$BASENAME = [System.IO.Path]::GetFileNameWithoutExtension($INPUT)
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$OUTPUT = "${BASENAME}_reviewed_${TIMESTAMP}.tex"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$AGENTS_DIR = Join-Path $SCRIPT_DIR "agents"
$PARENT_DIR = Resolve-Path (Join-Path $SCRIPT_DIR "..")
$DOCS_DIR = Resolve-Path (Join-Path $PARENT_DIR "docs")
$CHAPTERS_DIR = Resolve-Path (Join-Path $PARENT_DIR "chapters")
$REVIEW_DIR = Resolve-Path $SCRIPT_DIR

$READ_ALL = "`n---`nBefore starting, use the Read tool to read ALL files in the docs/ and review/ directories."
$READ_DOCS = "`n---`nBefore starting, use the Read tool to read ALL files in the docs/ directory."

Write-Host "=== Review started: $INPUT ==="
Write-Host "Output: $OUTPUT"
Write-Host ""

# --- [1/6] Educational Design ---
Write-Host "[1/6] Educational Design..."
$agent00 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "00_educational_design.md")
$sysprompt00 = $agent00 + $READ_ALL

$STEP00 = Get-Content -Raw -Encoding UTF8 $INPUT | claude --print --model opus --system-prompt $sysprompt00 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR --add-dir $CHAPTERS_DIR

# --- [2/6] Text Generation ---
Write-Host "[2/6] Text Generation..."
$agent01 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "01_text_generation.md")
$sysprompt01 = $agent01 + $READ_ALL

$STEP01 = $STEP00 | claude --print --model opus --system-prompt $sysprompt01 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR --add-dir $CHAPTERS_DIR

# --- [3/6] Rhythm & Writing ---
Write-Host "[3/6] Rhythm & Writing..."
$agent02 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "02_rhythm_writing.md")
$sysprompt02 = $agent02 + $READ_DOCS

$STEP02 = $STEP01 | claude --print --model opus --system-prompt $sysprompt02 --add-dir $DOCS_DIR

# --- [4/6] Statistical Accuracy ---
Write-Host "[4/6] Statistical Accuracy..."
$agent03 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "03_statistical_accuracy.md")
$sysprompt03 = $agent03 + $READ_ALL

$STEP03 = $STEP02 | claude --print --model opus --system-prompt $sysprompt03 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR

# --- [5/6] Structural Consistency ---
Write-Host "[5/6] Structural Consistency..."
$agent04 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "04_structural_consistency.md")
$sysprompt04 = $agent04 + $READ_ALL

$STEP04 = $STEP03 | claude --print --model opus --system-prompt $sysprompt04 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR --add-dir $CHAPTERS_DIR

# --- [6/6] Writing Quality ---
Write-Host "[6/6] Writing Quality..."
$agent05 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "05_writing_quality.md")
$sysprompt05 = $agent05 + $READ_DOCS

$STEP04 | claude --print --model opus --system-prompt $sysprompt05 --add-dir $DOCS_DIR | Out-File -Encoding UTF8 $OUTPUT

Write-Host ""
Write-Host "=== Done: $OUTPUT ==="
