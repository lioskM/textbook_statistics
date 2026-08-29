# リズム原則の全文Readを起草の前提条件として強制するhook。
# mark  (PostToolUse/Read): docs/リズム原則.md の Read ごとに実際に読めた行区間を記録し,
#        区間の和集合が全行をカバーした時点で「全文Read済み」マーカーを書く。
#        ハーネスは大きいファイルを切り詰める(PARTIAL view)ので, tool_input の limit/offset
#        ではなく tool_response の実カバー範囲を優先して数える。
# guard (PreToolUse/Edit|Write|NotebookEdit): 本文(chapters/*.tex)・言い回し標本・指示書・
#        リズム原則・要件定義書への書き込みを, 有効なマーカーがない限り deny する。
#        リズム原則が更新されるとマーカーと区間記録は無効になり, 読み直しが要る。
# 経緯: 2026-08-29, Ryosuke「仕組みとして強制的にそうしなければならないように縛っておいてください」。
#        判定役がv11を先頭300行のReadで済ませて60件を起草し, ペア群に記録済みの失敗を再演した件から。
#        導入直後, limitなしReadでもハーネスが450行で切り詰めてマーカーが付く偽陽性が見つかり,
#        区間の累積カバー方式に改めた。
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRINCIPLE = os.path.join(ROOT, "docs", "リズム原則.md")
STATE_DIR = os.path.join(ROOT, ".claude", "state")
DEFAULT_READ_LIMIT = 2000  # Read の既定行数


def principle_stamp():
    st = os.stat(PRINCIPLE)
    return f"{st.st_mtime_ns}:{st.st_size}"


def principle_lines():
    with open(PRINCIPLE, "rb") as f:
        return sum(1 for _ in f)


def sid_of(data):
    return re.sub(r"[^A-Za-z0-9_-]", "_", data.get("session_id", "") or "unknown")


def marker_path(sid):
    return os.path.join(STATE_DIR, f"rhythm_read_{sid}")


def cover_path(sid):
    return os.path.join(STATE_DIR, f"rhythm_cover_{sid}.json")


def deny(reason):
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))


def merged(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def mark(data):
    ti = data.get("tool_input") or {}
    fp = str(ti.get("file_path", "")).replace("\\", "/")
    if "リズム原則" not in fp:
        return
    stamp = principle_stamp()
    total = principle_lines()

    # 実カバー範囲: ハーネスの切り詰め表示があればそれを優先する。
    resp = json.dumps(data.get("tool_response", ""), ensure_ascii=False)
    m = re.search(r"showing lines (\d+)-(\d+) of (\d+)", resp)
    if m:
        start, end = int(m.group(1)), int(m.group(2))
    else:
        start = int(ti.get("offset") or 1) or 1
        limit = int(ti.get("limit") or DEFAULT_READ_LIMIT)
        end = min(start + limit - 1, total)

    os.makedirs(STATE_DIR, exist_ok=True)
    cov = {"stamp": stamp, "intervals": []}
    try:
        with open(cover_path(sid_of(data)), encoding="utf-8") as f:
            old = json.load(f)
        if old.get("stamp") == stamp:  # 原則が変わっていたら区間は捨てる
            cov = old
    except OSError:
        pass
    except Exception:
        pass
    cov["intervals"] = merged([list(map(int, iv)) for iv in cov["intervals"]] + [[start, end]])
    with open(cover_path(sid_of(data)), "w", encoding="utf-8") as f:
        json.dump(cov, f)

    ivs = cov["intervals"]
    if len(ivs) == 1 and ivs[0][0] <= 1 and ivs[0][1] >= total:
        with open(marker_path(sid_of(data)), "w", encoding="utf-8") as f:
            f.write(stamp)


def guard(data):
    ti = data.get("tool_input") or {}
    fp = str(ti.get("file_path", "")).replace("\\", "/")
    name_targets = ("言い回し標本", "指示書", "リズム原則", "要件定義書")
    is_target = ("/chapters/" in fp and fp.endswith(".tex")) or any(
        t in fp for t in name_targets
    )
    if not is_target:
        return
    try:
        with open(marker_path(sid_of(data)), encoding="utf-8") as f:
            recorded = f.read().strip()
    except OSError:
        deny(
            "【rhythm_guard】このセッションでは docs/リズム原則.md を全文Readしていない. "
            "本文・標本文書・指示書の起草/編集の前に, リズム原則を全文(ペア群と変更履歴まで, "
            "最終行に届くまで)読むこと. 表示が途中で切られたら offset を付けて続きを読む. "
            "全行に届けばこの編集は通る."
        )
        return
    if recorded != principle_stamp():
        deny(
            "【rhythm_guard】docs/リズム原則.md が全文Read後に更新されている. "
            "最新版を全文読み直してから編集すること."
        )


WRITE_TOKENS = (
    "sed -i", ">>", "> ", "tee ", ',"w"', ",'w'", '"w")', "'w')", "w+",
    "Out-File", "Set-Content", "Add-Content", "write_text", "io.open",
    "mv ", "cp ", "rm ", "shutil.", "truncate",
)
TARGET_NAMES = ("言い回し標本", "指示書", "リズム原則", "要件定義書", ".tex")


def guard_bash(data):
    # Bash/PowerShell 経由の書き込みで guard を迂回する穴を塞ぐ。
    # コマンド文字列に対象ファイル名と書き込みらしきトークンが両方あれば, マーカーを要求する。
    # 文字列ヒューリスティックなので完全ではない(一時ファイル経由の迂回等は検出できない)。
    # 主目的は「読まずに起草」の事故防止であって, 意図的な迂回への完全防御ではない。
    ti = data.get("tool_input") or {}
    cmd = str(ti.get("command", ""))
    if not any(t in cmd for t in TARGET_NAMES):
        return
    if not any(t in cmd for t in WRITE_TOKENS):
        return
    try:
        with open(marker_path(sid_of(data)), encoding="utf-8") as f:
            if f.read().strip() == principle_stamp():
                return
    except OSError:
        pass
    deny(
        "【rhythm_guard】シェル経由で本文・標本文書・指示書に書き込もうとしている可能性があるが, "
        "このセッションでは docs/リズム原則.md の全文Readが済んでいない(または原則が更新された). "
        "先にリズム原則を全文読むこと. 読み取り専用のコマンドが誤検知された場合は, "
        "リダイレクトや書き込み系トークンを含まない形に直せば通る."
    )


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        if mode == "guard":
            # 入力が読めないときは fail-close(拒否)に倒す。強制が目的のため。
            deny("【rhythm_guard】hook入力を解釈できなかったため, 安全側で拒否した.")
        return
    if mode == "mark":
        mark(data)
    elif mode == "guard":
        guard(data)
    elif mode == "guard_bash":
        guard_bash(data)


main()
