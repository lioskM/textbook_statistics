# 本文に触れたターンの終わりに, 段階を経たかの確認と, 面白さ・引きつけ・ユーモア・根本目的の事後確認を強制する Stop hook。
# 発火するのは, 本文 (chapters/*.tex)・図・指示書・言い回し標本への書き込み, git commit,
# または最終応答に本文の案 (コードブロック) を出したターンだけ。一度だけ停止を差し止める。
# 二度目の停止 (stop_hook_active) は通す (無限ループを避ける)。
# 経緯: 2026-10-01, 歴史の例 (バークレー, Literary Digest) を予備校の合格率とネット投票に差し替えたとき,
#        判定役は数字と論理の整合だけを見て「完了」と報告し, 面白いか・読者を引きつけるか・ユーモアが効いているか・
#        本の目的に適うかを確かめなかった。Ryosuke「hooksで絶対に事後確認するようにしてください。本当にあり得ない」。
# 2026-10-04 改定: 事後確認が欠けを「判断材料」として渡すだけで直らず, 起草依頼を送っただけのターンや
#        語の出現だけでも発火して読んでいない評価が増えた。Ryosuke「チェックしているだけで, チェックしてちゃんと直せていない」。
#        依頼の送信と語の出現では発火しないようにし, 案を出す前に 全体→部分→全体→部分 の段階 (部分は新しい文脈の
#        エージェントが一文ずつ読んで直した文を返す) を経たかを確かめさせ, 欠けを書いたら同じ応答で直した文を示させる。
import json
import re
import sys

EDIT_TOOLS = ("Edit", "Write", "NotebookEdit", "MultiEdit")
TARGET_PATH = re.compile(r"(/chapters/[^/]*\.tex$)|(/figures/)|指示書|言い回し標本")
DRAFT_IN_TEXT = re.compile(r"```")

CHECK_MSG = (
    "【hook・事後確認 (省略不可)】このターンは本文に触れた (tex の編集, commit, または本文の案の提示)。終える前に次の A〜C をやること。"
    "A. 本文の案を出したなら, その案が 全体→部分→全体→部分 の段階を経たかを確かめる。"
    "全体は, まず中身: (a) 章が通して言っていること (b) その節の受け持ち (c) docs/要件定義書.md §6 の該当段がその節に言わせると決めていること を書き出し, (d) 案がそれを言えているかを読む。"
    "そのあとでトーン (第1章から続く著者の声か) を見る。トーンは印象で見ず, 案の言い回しが第1章と著者本人の節に出てくるかを照らし, 出てこない言い回し (強める副詞, 飾り, 劇的な否定など) を一つずつその場所で読む。起草役には (c) を判定役が考えたうえで渡す。"
    "部分は, 前の判断を持たない新しい文脈のエージェントに第1章と対象の節と (a)(b) を渡し, "
    "日本語の読者として一文ずつ読ませ (その場所でその語を第1章の著者が言うか, 何が・何をが立っているか, docs/リズム原則.md の「繰り返し破られた線」に当たるか), 引っかかった文だけを直した文で返させる。"
    "そのあと直した文を段落に戻し, 前の節の終わりから次の節の頭まで通して読み, 崩れた所だけ直す。"
    "読み手が返した直した文と判定役が当てた直しも, 案に入れる前に「繰り返し破られた線」(とくに決め台詞の器, 「〜のは〜だ」の抽象締め, 包んでから指す形) に一文ずつ当てる。経ていなければ, 今それを経てから案を出し直す。"
    "B. 対象の各段落 (書いた・判定した・反映した段落) について, 文を現物から引き, 読者として読んだ結果を書く。"
    "(1) 読者が最初に思うことと, それを裏切るもの (なければ「驚きはない」) "
    "(2) 読者の返事を一言と, 次の文がそれに応えるか (場面の根が読者の実感にあるか) "
    "(3) 力の抜けた一言があるか (なければ「ない」. 押し付け・説教・決まり文句になっていないか) "
    "(4) 不確かさを確率で測り, それを含んだまま厳密に述べる, という理解が, この節の役目の範囲で一歩進むか。"
    "C. B で欠けを書いたら, 同じ応答の中で, その欠けを直した文を段落に置いて示す。直さないなら直さない理由を書く。"
    "欠けを判断材料として渡すだけで終えない。"
    "規則名・条番号で答えない。「完了」「問題なし」と書かない。対象の段落がなければ「対象なし」と書く。指示なく本文を編集しない。"
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
            elif name in ("Bash", "PowerShell"):
                if "git commit" in str(ti.get("command", "")):
                    return True
    return bool(last_text and DRAFT_IN_TEXT.search(last_text))


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
