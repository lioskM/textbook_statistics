# Textbook Review Pipeline (6-stage with Role A/B loop)
# Usage: powershell -ExecutionPolicy Bypass -File .\review\review.ps1 chapters\probability_distribution.tex
#
# Stages:
#   00 Educational Design  - produce question map, necessity chain, surprise points, examples
#   01 Text Generation     - generate LaTeX draft from design document
#   A/B Role A/B Loop      - reader feedback (Role A) -> writer rewrite (Role B), 1 iteration
#   03 Statistical Check   - verify statistical accuracy
#   04 Structural Check    - verify 6-step structure and cross-chapter consistency
#   05 Writing Quality     - final defense: prohibited words, anti-patterns
#
# Intermediate outputs are saved alongside the final output for inspection and debugging.

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

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$AGENTS_DIR = Join-Path $SCRIPT_DIR "agents"
$PARENT_DIR = Resolve-Path (Join-Path $SCRIPT_DIR "..")
$DOCS_DIR = Resolve-Path (Join-Path $PARENT_DIR "docs")
$CHAPTERS_DIR = Resolve-Path (Join-Path $PARENT_DIR "chapters")
$REVIEW_DIR = Resolve-Path $SCRIPT_DIR

# Intermediate outputs are saved in review/ directory
$STEP00_FILE = Join-Path $REVIEW_DIR "${BASENAME}_step00_${TIMESTAMP}.md"
$STEP01_FILE = Join-Path $REVIEW_DIR "${BASENAME}_step01_${TIMESTAMP}.tex"
$READER_REPORT_FILE = Join-Path $REVIEW_DIR "${BASENAME}_reader_report_${TIMESTAMP}.md"
$ROLE_B_FILE = Join-Path $REVIEW_DIR "${BASENAME}_step_ab_${TIMESTAMP}.tex"
$STEP03_FILE = Join-Path $REVIEW_DIR "${BASENAME}_step03_${TIMESTAMP}.tex"
$STEP04_FILE = Join-Path $REVIEW_DIR "${BASENAME}_step04_${TIMESTAMP}.tex"
$OUTPUT = Join-Path $REVIEW_DIR "${BASENAME}_reviewed_${TIMESTAMP}.tex"

$READ_ALL = "`n---`nDo NOT ask for permission. You already have access. Use the Read tool immediately to read ALL files in the docs/ and review/ directories, then proceed."
$READ_DOCS = "`n---`nDo NOT ask for permission. You already have access. Use the Read tool immediately to read ALL files in the docs/ directory, then proceed."

Write-Host "=== Review started: $INPUT ==="
Write-Host "Output: $OUTPUT"
Write-Host "Intermediate outputs in: $REVIEW_DIR"
Write-Host ""

# --- [1/6] Educational Design ---
Write-Host "[1/6] Educational Design..."
$agent00 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "00_educational_design.md")
$sysprompt00 = $agent00 + $READ_ALL

$STEP00 = Get-Content -Raw -Encoding UTF8 $INPUT | claude --print --model opus --system-prompt $sysprompt00 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR --add-dir $CHAPTERS_DIR
$STEP00 | Out-File -Encoding UTF8 $STEP00_FILE
Write-Host "  Saved: $STEP00_FILE"

# --- [2/6] Text Generation ---
Write-Host "[2/6] Text Generation..."
$agent01 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "01_text_generation.md")
$sysprompt01 = $agent01 + $READ_ALL

$STEP01 = $STEP00 | claude --print --model opus --system-prompt $sysprompt01 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR --add-dir $CHAPTERS_DIR
$STEP01 | Out-File -Encoding UTF8 $STEP01_FILE
Write-Host "  Saved: $STEP01_FILE"

# --- [3a/6] Role A: Reader feedback ---
Write-Host "[3a/6] Role A: Reader feedback..."
$roleA = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "role_a_reader.md")
$syspromptA = $roleA + $READ_DOCS

$READER_REPORT = $STEP01 | claude --print --model opus --system-prompt $syspromptA --add-dir $DOCS_DIR
$READER_REPORT | Out-File -Encoding UTF8 $READER_REPORT_FILE
Write-Host "  Saved: $READER_REPORT_FILE"

# --- [3b/6] Role B: Writer rewrite ---
Write-Host "[3b/6] Role B: Writer rewrite..."
$roleB = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "role_b_writer.md")
# Pass reader report via --add-dir; instruct Role B to read it
$roleB_instruction = "`n---`nDo NOT ask for permission. You already have access. Use the Read tool immediately to read ALL files in the docs/ directory AND the reader report at the following path, then proceed:`n$READER_REPORT_FILE"
$syspromptB = $roleB + $roleB_instruction

$STEP_AB = $STEP01 | claude --print --model opus --system-prompt $syspromptB --add-dir $DOCS_DIR --add-dir $REVIEW_DIR
$STEP_AB | Out-File -Encoding UTF8 $ROLE_B_FILE
Write-Host "  Saved: $ROLE_B_FILE"

# --- [4/6] Statistical Accuracy ---
Write-Host "[4/6] Statistical Accuracy..."
$agent03 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "03_statistical_accuracy.md")
$sysprompt03 = $agent03 + $READ_ALL

$STEP03 = $STEP_AB | claude --print --model opus --system-prompt $sysprompt03 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR
$STEP03 | Out-File -Encoding UTF8 $STEP03_FILE
Write-Host "  Saved: $STEP03_FILE"

# --- [5/6] Structural Consistency ---
Write-Host "[5/6] Structural Consistency..."
$agent04 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "04_structural_consistency.md")
$sysprompt04 = $agent04 + $READ_ALL

$STEP04 = $STEP03 | claude --print --model opus --system-prompt $sysprompt04 --add-dir $DOCS_DIR --add-dir $REVIEW_DIR --add-dir $CHAPTERS_DIR
$STEP04 | Out-File -Encoding UTF8 $STEP04_FILE
Write-Host "  Saved: $STEP04_FILE"

# --- [6/6] Writing Quality ---
Write-Host "[6/6] Writing Quality..."
$agent05 = Get-Content -Raw -Encoding UTF8 (Join-Path $AGENTS_DIR "05_writing_quality.md")
$sysprompt05 = $agent05 + $READ_DOCS

$STEP04 | claude --print --model opus --system-prompt $sysprompt05 --add-dir $DOCS_DIR | Out-File -Encoding UTF8 $OUTPUT

Write-Host ""
Write-Host "=== Done: $OUTPUT ==="
Write-Host ""
Write-Host "Intermediate outputs:"
Write-Host "  Stage 00 (educational design): $STEP00_FILE"
Write-Host "  Stage 01 (text generation):    $STEP01_FILE"
Write-Host "  Role A (reader report):        $READER_REPORT_FILE"
Write-Host "  Role B (writer rewrite):       $ROLE_B_FILE"
Write-Host "  Stage 03 (statistical):        $STEP03_FILE"
Write-Host "  Stage 04 (structural):         $STEP04_FILE"
Write-Host "  Final (writing quality):       $OUTPUT"
