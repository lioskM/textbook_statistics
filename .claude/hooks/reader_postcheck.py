# 本文にかかわる仕事をしたターンの終わりに, 面白さ・引きつけ・ユーモア・根本目的の事後確認を強制する Stop hook。
# 本文 (chapters/*.tex)・図・指示書・言い回し標本への書き込み, 起草・反映・判定の委任 (Agent/SendMessage),
# git commit, または最終応答に本文の案が出たターンでは, 一度だけ停止を差し止め, 最終応答に事後確認を書かせる。
# 二度目の停止 (stop_hook_active) は通す (無限ループを避ける)。
# 経緯: 2026-10-01, 歴史の例 (バークレー, Literary Digest) を予備校の合格率とネット投票に差し替えたとき,
#        判定役は数字と論理の整合だけを見て「完了」と報告し, 面白いか・読者を引きつけるか・ユーモアが効いているか・
#        本の目的に適うかを確かめなかった。Ryosuke「hooksで絶対に事後確認するようにしてください。本当にあり得ない」。
import json
import re
import sys

EDIT_TOOLS = ("Edit", "Write", "NotebookEdit", "MultiEdit")
TARGET_PATH = re.compile(r"(/chapters/[^/]*\.tex$)|(/figures/)|指示書|言い回し標本")
DELEGATE_TOOLS = ("Agent", "Task", "SendMessage")
DELEGATE_WORDS = re.compile(r"起草|修正案|反映|指示書|本文|判定|差し替え|書き直")
TEXT_WORDS = re.compile(r"修正案|差し替え|起草|書き直し|本文の案|例を|場面")

CHECK_MSG = (
    "【hook・事後確認 (省略不可)】このターンは本文にかかわる仕事をした。終える前に, 最終応答に次の事後確認を書くこと。"
    "対象は, このターンで書いた・判定した・反映した本文の各段落。段落の文を現物から引いて, その下に読者として読んだ結果を書く。"
    "(1) 面白いか: 読者が最初に何を思っていて, この段落の何がそれを裏切るか。裏切りがなければ「驚きはない」と書く。"
    "(2) 読者を引きつけるか: 読者はこの段落を読みたいと思うか。場面の根が読者の実感 (本書の通し例, 読者の生活) にあるか, "
    "読者がもう知っていることを著者が思い込ませていないか。段落ごとに読者の返事を一言書き, 次の文がそれに応えるかを見る。"
    "(3) ユーモアが効いているか: 力の抜けた一言があるか, 押し付け・説教・決まり文句になっていないか。なければ「ない」と書く。"
    "(4) 根本目的に適うか: 不確かさを確率で測り, それを含んだまま厳密に述べる (要件定義書 §2) という理解が, この段落で読者の中に一歩進むか。"
    "規則名・条番号で答えない。自分の読みで書き, 足りないものは足りないと書く。判定役は面白さを自分では決められないので, "
    "判断材料 (現物の文と, 読者の側から見た欠け) を Ryosuke が決められる形で示す。足りない点があるのに「完了」「問題なし」と報告しない。"
    "直すための案は示してよいが, 指示なく本文を編集しない。"
)


def load_turn(path):
    """transcript から, 最後の本物のユーザー発話より後のエントリを返す。"""
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    continue
    except Exception:
        return []
    start = 0
    for i, r in enumerate(rows):
        if r.get("type") != "user" or r.get("isMeta") or r.get("isCompactSummary"):
            continue
        c = (r.get("message") or {}).get("content")
        if isinstance(c, str):
            start = i + 1
        elif isinstance(c, list) and not any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in c
        ):
            start = i + 1
    return rows[start:]


def triggered(turn, last_text):
    for r in turn:
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            name = b.get("name", "")
            ti = b.get("input") or {}
            if name in EDIT_TOOLS:
                fp = str(ti.get("file_path", "")).replace("\\", "/")
                if TARGET_PATH.search(fp):
                    return True
            elif name in DELEGATE_TOOLS:
                body = " ".join(str(ti.get(k, "")) for k in ("prompt", "message", "description"))
                if DELEGATE_WORDS.search(body):
                    return True
            elif name in ("Bash", "PowerShell"):
                if "git commit" in str(ti.get("command", "")):
                    return True
    return bool(last_text and TEXT_WORDS.search(last_text))


def last_assistant_text(data, turn):
    t = data.get("last_assistant_message")
    if isinstance(t, str) and t:
        return t
    for r in reversed(turn):
        if r.get("type") != "assistant":
            continue
        texts = [
            b.get("text", "")
            for b in (r.get("message") or {}).get("content") or []
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        if texts:
            return "\n".join(texts)
    return ""


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return
    if data.get("stop_hook_active"):
        return
    turn = load_turn(data.get("transcript_path", ""))
    if not triggered(turn, last_assistant_text(data, turn)):
        return
    out = {"decision": "block", "reason": CHECK_MSG}
    sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))


main()
