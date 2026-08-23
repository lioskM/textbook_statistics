# -*- coding: utf-8 -*-
"""文体検査器 — リズム原則v7・要件定義書v16の確定規則のうち機械判定可能なものを走査する.

二層構成:
  block: 確定済みの禁止規則. 新規・修正行に混入したらコミットを止める (pre-commit / Codexループの終了条件).
  flag : ヒューリスティック. 候補を報告するだけで止めない. 採否は判定の場で決める.

条文化禁止の原則に従い, この検査器は「網」であって「審判」ではない.
flag層の検出ゼロを目標にしてはならない (リズム原則§4: 原則の充足は品質の必要条件ですらない).

使い方:
  uv run python tools/style_check.py --all              # chapters/*.tex 全走査 (報告のみ)
  uv run python tools/style_check.py --files a.tex ...  # 指定ファイル走査 (block検出で exit 1)
  uv run python tools/style_check.py --staged           # git のステージ済み追加行のみ (block検出で exit 1)
"""
import argparse
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (id, 層, 正規表現, 説明, 出典)
RULES = [
    # ---- block: 確定済み禁止 ----
    ("yureru",      "block", r"揺れ(る|た|て|方)", "禁止語「揺れる」→ ばらつく・散らばる等", "要件定義書§4.4"),
    ("emdash",      "block", r"[—―]", "emダッシュ禁止", "要件定義書§4.4"),
    ("michi",       "block", r"道が開け", "「道が開ける」禁止", "要件定義書§4.4"),
    ("gyakuyomi",   "block", r"逆から読む", "「これを逆から読む」禁止", "要件定義書§4.4"),
    ("suisoku",     "block", r"推測統計|記述統計", "「推測統計/記述統計」の枠組み禁止", "要件定義書§4.4"),
    ("kakizoe",     "block", r"書き添え", "複合動詞の借り物の上品さ.「書く」で足りる", "リズム原則§3格/第5章標本13"),
    ("yarikata",    "block", r"やり方", "口語「やり方」→「方法」", "リズム原則§3格/第2章較正欄"),
    ("dougu",       "block", r"道具", "手法を「道具」と呼ばない (解消済み. 再発防止)", "要件定義書用語指針/コミット98ef1a7"),
    ("kyoukun",     "block", r"教訓", "「〜は教訓になる」型の教訓化を書かない", "feedback-history-column/第6章標本20"),
    ("toyomeru",    "block", r"と読める", "可能形の評言「〜と読める」→ 事実陳述に戻す", "feedback-toi-yomeru 2026-08-16"),
    ("ch-ref",      "block", r"第?\d+章", "章番号参照を書かない (既存分の削除は全書トラックで個別判断)", "リズム原則§3/第5章標本15"),
    ("tokoromade",  "block", r"ところまで(進|来|行|終)", "抽象語の締め「〜ところまで進む」型", "feedback-abstract-ending"),
    ("sample-size", "block", r"サンプルサイズ|サンプル・サイズ", "表記は「標本サイズ」", "要件定義書§4.9"),
    # ---- flag: ヒューリスティック (候補出しのみ) ----
    ("toi",         "flag", r"問い(?!合わせ)", "講義語「問い」の疑い. 抽象的な用法が多いが可の場合もある", "feedback-toi-yomeru 2026-08-16"),
    ("se-jibun",    "flag", r"\$\\mathrm\{SE\}\$", "地の文の$\\mathrm{SE}$の疑い. 記号導入・数式内は正用", "リズム原則§3格/第5章標本10・13"),
    ("gijinka",     "flag", r"(図|データ|統計量|平均|分散|標準偏差|区間|検定|数字|グラフ|ヒストグラム)(が|は)[^.。,、]{0,12}(語|答え|教え|拾|返し|返す|伝え|呼び起こ|連れて|姿を見せ|くれ)", "擬人化の疑い (表す・示すは可)", "リズム原則§3翻訳調"),
    ("ochiru",      "flag", r"に落ち", "範囲用法の「落ちる」の疑い (欠落の意味は正用)", "要件定義書§4.4"),
    ("meishika",    "flag", r"すること(が|を|に)|(読み方|作り方)(を|が|は)", "名詞化の疑い. 動詞にほどけないか", "リズム原則§3接地/第5章標本2・9"),
    ("nouryoku",    "flag", r"できるようになった|手に入れた|見えてくる", "能力獲得・状態変化の宣言の疑い (詠嘆優先で残す例あり)", "リズム原則§3翻訳調/ペア4"),
    ("shigoto",     "flag", r"の仕事", "workの直訳「仕事」の疑い", "リズム原則§3翻訳調"),
    ("mizumashi",   "flag", r"として機能する|役割を果た|において重要", "意義の水増し", "要件定義書§4.5"),
    ("filler",      "flag", r"という点において|であると言える|ということになる", "filler", "要件定義書§4.5"),
    ("hedge",       "flag", r"かもしれないと考えることもでき", "多重ヘッジ", "要件定義書§4.5"),
    ("retsukyo",    "flag", r"\\begin\{(itemize|enumerate)\}", "列挙形式. 地の文を箇条書きで流していないか", "feedback-ai-japanese-patterns 2026-08-16"),
    ("butsun",      "flag", r"(?:^|[.。])\s*([^.。「」『』()（）,、\s%$\\]{2,6}(?:る|く|す|う|つ|む|ぶ|ぐ))[.。]", "ぶつん切れの疑い (短文の動詞断定止め)", "feedback-butsun-ending/リズム原則§3終わり方"),
]

COMPILED = [(rid, sev, re.compile(pat), desc, src) for rid, sev, pat, desc, src in RULES]


def read_lines(path):
    for enc in ("utf-8", "cp932"):
        try:
            with open(path, encoding=enc) as f:
                return f.read().splitlines()
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"エンコーディングを判別できない: {path}")


def scan_line(line):
    """1行を走査して (rule_id, 層, 説明, マッチ文字列) を返す. コメント行は対象外."""
    if line.lstrip().startswith("%"):
        return
    for rid, sev, rx, desc, src in COMPILED:
        for m in rx.finditer(line):
            yield rid, sev, desc, m.group(0)


def scan_files(paths):
    hits = []
    for path in paths:
        rel = os.path.relpath(path, ROOT)
        for i, line in enumerate(read_lines(path), 1):
            for rid, sev, desc, frag in scan_line(line):
                hits.append((rel, i, rid, sev, desc, frag))
    return hits


def scan_staged():
    """ステージ済み diff の追加行のみ走査する.

    持ち越し判定: 追加行に出た block 語が, 同じファイルの削除行にも含まれるなら,
    既存参照の持ち越し (行の書き換えに伴う再検出) とみなして flag に降格する.
    新規の持ち込みは従来どおり block (リズム原則§4 機械検査層の注意の恒久対応).
    """
    out = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--", "chapters/*.tex"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    ).stdout
    removed = {}
    path = None
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
            removed.setdefault(path, [])
        elif raw.startswith("-") and not raw.startswith("---") and path is not None:
            removed[path].append(raw[1:])
    hits = []
    path, lineno = None, 0
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            lineno = int(m.group(1)) if m else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            for rid, sev, desc, frag in scan_line(raw[1:]):
                if sev == "block" and any(frag in old for old in removed.get(path, [])):
                    sev, desc = "flag", desc + " (削除行にも同語あり: 既存の持ち越し)"
                hits.append((path, lineno, rid, sev, desc, frag))
            lineno += 1
        elif not raw.startswith("-"):
            lineno += 1
    return hits


def report(hits, verbose):
    blocks = [h for h in hits if h[3] == "block"]
    flags = [h for h in hits if h[3] == "flag"]
    for group, name in ((blocks, "block (確定禁止)"), (flags, "flag (要判定の候補)")):
        if not group:
            continue
        print(f"== {name}: {len(group)}件 ==")
        if verbose or name.startswith("block"):
            for rel, i, rid, _, desc, frag in group:
                print(f"  {rel}:{i} [{rid}] {frag!r} — {desc}")
        else:
            counts = {}
            for rel, i, rid, _, desc, frag in group:
                counts[rid] = counts.get(rid, 0) + 1
            for rid, n in sorted(counts.items(), key=lambda kv: -kv[1]):
                desc = next(d for r, s, p, d, o in RULES if r == rid)
                print(f"  [{rid}] {n}件 — {desc}")
    if not hits:
        print("検出なし.")
    return bool(blocks)


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="chapters/*.tex を全走査 (報告のみ, exit 0)")
    mode.add_argument("--staged", action="store_true", help="ステージ済み追加行のみ (block検出で exit 1)")
    mode.add_argument("--files", nargs="+", help="指定ファイルを走査 (block検出で exit 1)")
    ap.add_argument("-v", "--verbose", action="store_true", help="flag層も逐件表示")
    args = ap.parse_args()

    if args.all:
        hits = scan_files(sorted(glob.glob(os.path.join(ROOT, "chapters", "*.tex"))))
        report(hits, args.verbose)
        return 0
    if args.staged:
        has_block = report(scan_staged(), args.verbose)
    else:
        has_block = report(scan_files(args.files), args.verbose)
    if has_block:
        print("\nblock層の検出があります. 修正してから再実行してください.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
