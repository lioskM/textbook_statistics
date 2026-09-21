# リズム原則と周辺文書の全文Readを, 起草の前提条件として強制するhook。
# mark  (PostToolUse/Read): 必読文書の Read ごとに実際に読めた行区間を記録し,
#        区間の和集合が全行をカバーした時点でその文書の「全文Read済み」を記録する。
#        ハーネスは大きいファイルを切り詰める(PARTIAL view)ので, tool_input の limit/offset
#        ではなく tool_response の実カバー範囲を優先して数える。
# guard (PreToolUse/Edit|Write|NotebookEdit): 本文(chapters/*.tex)・言い回し標本・指示書・
#        リズム原則・要件定義書への書き込みを, 必読文書の全部に有効な記録がない限り deny する。
#        文書が更新されると記録は無効になり, 読み直しが要る。
# 必読文書: docs/リズム原則.md (v15 で絶対則・判定原則・翻訳調の族・memory の feedback 群を一つに畳んだ),
#        docs/要件定義書.md, docs/概念導入順序整理.md。
#        2026-09-12, Ryosuke「すべて一つの書類にまとめてください」。memory の feedback_*.md は必読から外し,
#        内容はリズム原則「繰り返し破られた線」が持つ。
# 経緯: 2026-08-29, Ryosuke「仕組みとして強制的にそうしなければならないように縛っておいてください」。
#        判定役がv11を先頭300行のReadで済ませて60件を起草し, ペア群に記録済みの失敗を再演した件から。
#        導入直後, limitなしReadでもハーネスが450行で切り詰めてマーカーが付く偽陽性が見つかり,
#        区間の累積カバー方式に改めた。
#        2026-09-06, Ryosuke「hookで必ずリズム原則を徹底して読むことを指示し, 周辺まで含めて読むように
#        してください。もう本当に話になりません」。トラック4で判定役の見出し案が四度差し戻され,
#        リズム原則を読んだ後でも基準が起草に効いていなかった件から, 必読を周辺文書と memory まで広げた。
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, ".claude", "state")
DEFAULT_READ_LIMIT = 2000  # Read の既定行数

# プロジェクト内の必読文書 (key, path)
PROJECT_DOCS = [
    ("リズム原則", os.path.join(ROOT, "docs", "リズム原則.md")),
    ("要件定義書", os.path.join(ROOT, "docs", "要件定義書.md")),
    ("概念導入順序整理", os.path.join(ROOT, "docs", "概念導入順序整理.md")),
]


def memory_dir():
    """Claude Code の auto-memory ディレクトリを探す。見つからなければ None。"""
    env = os.environ.get("CLAUDE_MEMORY_DIR")
    if env and os.path.isdir(env):
        return env
    home = os.path.expanduser("~")
    base = os.path.join(home, ".claude", "projects")
    # プロジェクトパスをエンコードした名前(例: c--Users-...-textbook-statistics)を含むものを探す
    # エンコード名は '_' が '-' になる(textbook_statistics → textbook-statistics)
    tail = os.path.basename(ROOT).lower().replace("_", "-")
    cands = sorted(glob.glob(os.path.join(base, "*", "memory")))
    for c in cands:
        if tail in os.path.basename(os.path.dirname(c)).lower().replace("_", "-"):
            return c
    return None


def memory_docs():
    d = memory_dir()
    if not d:
        return []
    out = []
    for p in sorted(glob.glob(os.path.join(d, "feedback_*.md"))):
        out.append((os.path.basename(p), p))
    return out


def required_docs():
    # v15 以降, memory の feedback 群はリズム原則に畳まれたので必読に含めない。
    return PROJECT_DOCS


def stamp_of(path):
    st = os.stat(path)
    return f"{st.st_mtime_ns}:{st.st_size}"


def lines_of(path):
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def sid_of(data):
    return re.sub(r"[^A-Za-z0-9_-]", "_", data.get("session_id", "") or "unknown")


def state_path(sid):
    return os.path.join(STATE_DIR, f"rhythm_state_{sid}.json")


def load_state(sid):
    try:
        with open(state_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(sid, st):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(state_path(sid), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False)


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


def match_doc(fp):
    """Read された file_path が必読文書のどれかを返す。"""
    fp_n = fp.replace("\\", "/").lower()
    for key, path in required_docs():
        p_n = path.replace("\\", "/").lower()
        if fp_n == p_n or fp_n.endswith("/" + os.path.basename(p_n)):
            return key, path
    return None, None


def mark(data):
    ti = data.get("tool_input") or {}
    fp = str(ti.get("file_path", ""))
    key, path = match_doc(fp)
    if not key:
        return
    stamp = stamp_of(path)
    total = lines_of(path)

    # 実カバー範囲: ハーネスの切り詰め表示があればそれを優先する。
    resp = json.dumps(data.get("tool_response", ""), ensure_ascii=False)
    m = re.search(r"showing lines (\d+)-(\d+) of (\d+)", resp)
    if m:
        start, end = int(m.group(1)), int(m.group(2))
    else:
        start = int(ti.get("offset") or 1) or 1
        limit = int(ti.get("limit") or DEFAULT_READ_LIMIT)
        end = min(start + limit - 1, total)

    sid = sid_of(data)
    st = load_state(sid)
    rec = st.get(key) or {}
    if rec.get("stamp") != stamp:  # 文書が変わっていたら区間は捨てる
        rec = {"stamp": stamp, "intervals": [], "done": False}
    rec["intervals"] = merged([list(map(int, iv)) for iv in rec["intervals"]] + [[start, end]])
    ivs = rec["intervals"]
    rec["done"] = bool(len(ivs) == 1 and ivs[0][0] <= 1 and ivs[0][1] >= total)
    st[key] = rec
    save_state(sid, st)


def unread(sid):
    """未読または更新後未読の必読文書を [(key, 状況)] で返す。"""
    st = load_state(sid)
    out = []
    for key, path in required_docs():
        if not os.path.exists(path):
            continue
        rec = st.get(key)
        if not rec:
            out.append((key, "未読"))
            continue
        if rec.get("stamp") != stamp_of(path):
            out.append((key, "Read後に更新あり"))
            continue
        if not rec.get("done"):
            cov = ", ".join(f"{s}-{e}" for s, e in rec.get("intervals", []))
            out.append((key, f"途中まで({cov} / 全{lines_of(path)}行)"))
    return out


def all_read(sid):
    return not unread(sid)


REQUIRE_MSG = (
    "起草/編集の前に必読文書を全文読むこと: docs/リズム原則.md(§0 と「繰り返し破られた線」からペア群と変更履歴まで最終行に届くまで), "
    "docs/要件定義書.md, docs/概念導入順序整理.md。"
    "表示が途中で切られたら offset を付けて続きを読む。全部に届けばこの編集は通る。"
)


def guard(data):
    ti = data.get("tool_input") or {}
    fp = str(ti.get("file_path", "")).replace("\\", "/")
    name_targets = ("言い回し標本", "指示書", "リズム原則", "要件定義書")
    is_target = ("/chapters/" in fp and fp.endswith(".tex")) or any(
        t in fp for t in name_targets
    )
    if not is_target:
        return
    miss = unread(sid_of(data))
    if miss:
        detail = "; ".join(f"{k}: {s}" for k, s in miss)
        deny(f"【rhythm_guard】必読文書に未読がある → {detail}. " + REQUIRE_MSG)


WRITE_TOKENS = (
    "sed -i", ">>", "> ", "tee ", ',"w"', ",'w'", '"w")', "'w')", "w+",
    "Out-File", "Set-Content", "Add-Content", "write_text", "io.open",
    "mv ", "cp ", "rm ", "shutil.", "truncate",
)
TARGET_NAMES = ("言い回し標本", "指示書", "リズム原則", "要件定義書", ".tex")


def guard_bash(data):
    # Bash/PowerShell 経由の書き込みで guard を迂回する穴を塞ぐ。
    # コマンド文字列に対象ファイル名と書き込みらしきトークンが両方あれば, 全文Readを要求する。
    # 文字列ヒューリスティックなので完全ではない(一時ファイル経由の迂回等は検出できない)。
    # 主目的は「読まずに起草」の事故防止であって, 意図的な迂回への完全防御ではない。
    ti = data.get("tool_input") or {}
    cmd = str(ti.get("command", ""))
    if not any(t in cmd for t in TARGET_NAMES):
        return
    if not any(t in cmd for t in WRITE_TOKENS):
        return
    miss = unread(sid_of(data))
    if miss:
        detail = "; ".join(f"{k}: {s}" for k, s in miss)
        deny(
            "【rhythm_guard】シェル経由で本文・標本文書・指示書に書き込もうとしている可能性があるが, "
            f"必読文書に未読がある → {detail}. " + REQUIRE_MSG +
            " 読み取り専用のコマンドが誤検知された場合は, リダイレクトや書き込み系トークンを含まない形に直せば通る."
        )


def short_name(path):
    if path.startswith(ROOT):
        return os.path.relpath(path, ROOT).replace("\\", "/")
    return "memory/" + os.path.basename(path)


APPLY_MSG = (
    "【hook・判定の形】修正案を判定するときは, 修正前と修正案を段落の中に置いて自分で二度読み, 最初の一文を"
    "「読者として残すのはどちらか」と「その段落で読者に何が起きるか」で書く。その一文に規則名・条番号・族名・"
    "「意味が変わる」「統計的主張」を書いてはならない。規則は基準の記録であって, 規則に照らした結果は判定ではない。"
    "自分の読みで出し, 外れたら外れたと言う。規則の後ろに隠れた判定は, 正しく見えても出さない。"
    "(Ryosuke 2026-09-13「考えなく, このルールを守っていればよいと浅はかに認識しているのではないですか」) "
    "【hook】読むだけでなく当てること。起草の前に: (1) 読者が見る場所(目次/段落/章)を決め, "
    "(2) その場所の裁定済みの現物を読み, (3) 対象を一語で確定してから書き, (4) 案をその場所に置いて読む。"
    "差し戻しを受けたら局所を直さず束全体を起草し直し, 直前の指摘ではなくリズム原則 §0・「繰り返し破られた線」・§4 を読み直す。"
    "見出しを起草するときは全章の見出し一覧(目次)を先に読む。"
)


def scope_msg():
    """docs/リズム原則.md §0.1「絶対則」を一行に畳んで返す。Claude Code, Codex (AGENTS.md), Gemini (GEMINI.md) で同じ文書を使う。"""
    p = os.path.join(ROOT, "docs", "リズム原則.md")
    try:
        with open(p, encoding="utf-8") as f:
            text = f.read()
        i = text.index("### 0.1 絶対則")
        j = text.index("### 0.2", i)
        body = [ln.strip() for ln in text[i:j].splitlines()[1:] if ln.strip()]
        return "【hook・絶対則】" + " ".join(body) + " 判定は二読で行う: 一読目は全体（読者として通して読み, 採否を決める。規則は見ない）, 二読目は局所（「繰り返し破られた線」で残った語を名づけ, その語だけ直す）。二読目で一読目の採否を覆さない。"
    except Exception:
        return "【hook・絶対則】docs/リズム原則.md §0 を読んで従うこと(hook が読めなかった)。"


SCOPE_MSG = scope_msg()


def design_msg():
    """docs/要件定義書.md「## 0. 設計の観点」を一行に畳んで返す。すべての依頼より上位に置く (Ryosuke 2026-09-21)。"""
    p = os.path.join(ROOT, "docs", "要件定義書.md")
    try:
        with open(p, encoding="utf-8") as f:
            text = f.read()
        i = text.index("## 0. 設計の観点")
        j = text.index("\n---", i)
        body = [ln.strip() for ln in text[i:j].splitlines()[1:] if ln.strip()]
        return "【hook・設計の観点 (すべての依頼より上位)】" + " ".join(body)
    except Exception:
        return "【hook・設計の観点】docs/要件定義書.md §0 を読んで従うこと(hook が読めなかった)。"


DESIGN_MSG = design_msg()


def status(data):
    """SessionStart 用: 必読文書の一覧と現在の既読状況を全件出力する。"""
    sid = sid_of(data)
    miss = dict(unread(sid))
    print(DESIGN_MSG)
    print(SCOPE_MSG)
    print("【hook】本文の修正案・差し替え文・見出しを起草する前に, 次の必読文書を全文読むこと(切り詰められたら offset で続きを読み, 最終行に届くまで)。未読があるあいだ, 本文・標本文書・指示書への書き込みは拒否される。")
    for key, path in required_docs():
        if not os.path.exists(path):
            continue
        print(f"  - {short_name(path)} ({lines_of(path)}行) : {miss.get(key, '既読')}")
    print(APPLY_MSG)


def remind(data):
    """UserPromptSubmit 用: 未読分だけを短く出す。"""
    sid = sid_of(data)
    miss = unread(sid)
    docs = dict(required_docs())
    print(DESIGN_MSG)
    print(SCOPE_MSG)
    if miss:
        names = ", ".join(f"{short_name(docs[k])}({s})" for k, s in miss)
        print(f"【hook】必読文書に未読 {len(miss)} 件: {names}。起草/編集の前に全文読むこと。")
    else:
        print("【hook】必読文書は全件既読。")
    print(APPLY_MSG)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        if mode == "guard":
            # 入力が読めないときは fail-close(拒否)に倒す。強制が目的のため。
            deny("【rhythm_guard】hook入力を解釈できなかったため, 安全側で拒否した.")
            return
        data = {}
    if mode == "mark":
        mark(data)
    elif mode == "guard":
        guard(data)
    elif mode == "guard_bash":
        guard_bash(data)
    elif mode == "status":
        status(data)
    elif mode == "remind":
        remind(data)


main()
