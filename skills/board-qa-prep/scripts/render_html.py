"""The board_qa key as one self-contained HTML page in the Leader Report style guide, and its Markdown twin.

The page takes the report's whole stylesheet from its template (assets/vendor/template.html, vendored
byte-identical at a pinned commit), so it is the same brand family as the deck. It follows the report's
references/design.md: mono capitals for labels, sans for sentences, hairlines not boxes. Green, grey-white and
red mean a bet's status only, and appear once, on the status did-it-land set. Brass marks a person's call: an
open question's owner and due date. Check chips, answered and open alike, are ink, never a status colour.

Nothing is loaded from the network, nothing depends on the clock or the machine, and every piece of text from
the record is escaped.

Standard library only. Python 3.11 or later.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from display import num

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "vendor" / "template.html"
STYLE = re.compile(r"<style>(.*?)</style>", re.S)
CITE = re.compile(r"\s*\[(F\d{1,3})\]")

PAGE_CSS = """
/* The vendored template paints selection and focus green; green is kept for the bet status, so both print in ink here. */
::selection{background:var(--t1);color:var(--bg)}
:focus-visible{outline-color:var(--t1)}
main.solo{margin-left:0}
.solo .slide{min-height:0}
.solo .slide.cover{padding-top:72px;padding-bottom:40px}
.solo .lede{margin-bottom:8px}
.qa{margin-top:4px}
.qa>div{display:grid;grid-template-columns:56px minmax(0,1fr) 92px;gap:6px 28px;border-top:1px solid var(--line);padding:16px 0}
.qa .id{font:400 10px/22px var(--mono);letter-spacing:.1em;color:var(--t3)}
.qa .q{color:var(--t1);font-size:15px;line-height:1.45}
.qa .a{display:block;color:var(--t2);font-size:13.5px;margin-top:6px;max-width:78ch}
.qa .k{display:block;font:400 10px/16px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--t3);margin-top:8px}
.qa .w{text-align:right}
.chip.answered{color:var(--t1);border-color:var(--line3)}
.chip.open{color:var(--t1);border-color:var(--line3);border-style:dashed}
.own{display:block;font:400 11.5px/18px var(--mono);color:var(--brass);margin-top:8px}
.own i{font-style:normal;font-size:10px;letter-spacing:.1em;color:var(--t3);margin-right:6px}
.own i+i{margin-left:18px}
.facts span.st{display:inline-flex;flex-direction:row;align-items:center;gap:8px;font-size:12px;line-height:30px}
.keys td:first-child{font-family:var(--mono);font-size:11.5px}
.answer{font-size:19px;line-height:1.4;color:var(--t1);margin:0 0 14px;max-width:64ch}
.sum{list-style:none;margin:0 0 20px;padding:0;max-width:78ch}
.sum li{border-top:1px solid var(--line);padding:7px 0;font-size:13.5px;color:var(--t2)}
.sum li b{font:400 10px/18px var(--mono);letter-spacing:.1em;color:var(--t3);margin-right:10px}
.more{border-top:1px solid var(--line);padding:14px 0}
.more>summary{cursor:pointer;font:400 11px/20px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t2)}
.more>summary:hover{color:var(--t1)}
.more[open]>summary{margin-bottom:8px}
.foot{max-width:1120px;margin:0 auto;padding:28px 40px 64px;color:var(--t3);font-size:12px}
@media (max-width:980px){.qa>div{grid-template-columns:1fr;gap:4px}.qa .w{text-align:left}.foot{padding:24px 16px 48px}.solo .slide.cover{padding-top:48px}}
"""

MARK = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">'
    '<rect x="2" y="13" width="3" height="7" fill="var(--agent)"/><rect x="7" y="10" width="3" height="10" fill="var(--agent)"/>'
    '<rect x="12" y="2" width="1.5" height="20" fill="var(--brass)"/><rect x="16" y="4" width="4" height="16" fill="var(--t1)"/></svg>'
)
WRITER_LABEL = {
    "portfolio": "bet-portfolio-review",
    "decisions": "decision-record",
    "spec": "spec-auditor",
    "release": "release-readiness",
    "cost": "cost-budget-check",
    "evals": "eval-kit",
    "landed": "did-it-land",
    "signals": "customer-signal-digest",
    "postmortem": "postmortem",
}


def e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def stylesheet() -> str:
    try:
        found = STYLE.search(TEMPLATE.read_text(encoding="utf-8"))
    except OSError:
        found = None
    return found.group(1) if found else ""


def cites(text: str) -> str:
    """Escaped text with each [F01] drawn as the report's ledger tag."""
    out, last = [], 0
    for m in CITE.finditer(text):
        out.append(e(text[last : m.start()]))
        out.append(f'<a class="led" href="#{e(m.group(1))}">{e(m.group(1))}</a>')
        last = m.end()
    out.append(e(text[last:]))
    return "".join(out)


def written_by(record: dict[str, Any], key: str) -> tuple[str, str]:
    """(tool and version, as_of) a key says it was written by, as it says it."""
    k = record.get(key) or {}
    tool = k.get("tool") or k.get("computed_by") or " ".join(str(x) for x in (k.get("skill"), k.get("skill_version") or k.get("version")) if x) or WRITER_LABEL[key]
    if key == "spec" and k.get("version") and str(k.get("version")) not in str(tool):
        tool = f"{tool} {k['version']}"
    return str(tool), str(k.get("as_of") or "")[:10]


def answer_line(k: dict[str, Any]) -> str:
    """The point in one line: how many of the likely questions the record answers, and how many need a person."""
    n = {name: f["value"] for name, f in k["counts"].items()}
    if not n["open"]:
        return f"All {n['questions']} likely questions are answered from the loop record."
    need = "needs an answer" if n["open"] == 1 else "need an answer"
    return f"{n['answered']} of {n['questions']} likely questions are answered from the loop record; {n['open']} {need} from their owner before the meeting."


def summary_lines(k: dict[str, Any]) -> list[tuple[str, str]]:
    """One line per question to prepare first: (id, the question and where it stands)."""
    qs = {q["id"]: q for q in k["questions"]}
    out = []
    for i in k["first"]:
        q = qs[i]
        where = f"open, owner {q['owner']}, due {q['due']}" if q["check"] == "open" else "answered from the record"
        if q["check"] == "answered" and q.get("stated_by"):
            where = f"answered, stated by {q['stated_by']}"
        out.append((i, f"{q['question']} ({where})"))
    return out


def row(q: dict[str, Any]) -> str:
    body = q.get("answer") if q["check"] == "answered" else q.get("missing")
    extra = ""
    if q["check"] == "open":
        extra = f'<span class="own"><i>OWNER</i>{e(q["owner"])}<i>DUE</i>{e(q["due"])}</span>'
    elif q.get("stated_by"):
        extra = f'<span class="k">Stated by {e(q["stated_by"])}</span>'
    asked = '<span class="k">Asked at the last meeting</span>' if q.get("asked_last_time") else ""
    return (
        f'<div id="{e(q["id"])}"><span class="id">{e(q["id"])}</span>'
        f'<span><span class="q">{e(q["question"])}</span><span class="a">{cites(str(body or ""))}</span>{extra}{asked}</span>'
        f'<span class="w"><span class="chip {e(q["check"])}">{e(q["check"])}</span></span></div>'
    )


def page(record: dict[str, Any]) -> str:
    k = record["board_qa"]
    qs = {q["id"]: q for q in k["questions"]}
    n = {name: f["value"] for name, f in k["counts"].items()}
    title = f"Board questions: {k['bet_title']}"
    meta = "".join(f"<span>{e(m)}</span>" for m in (f"As of {k['as_of']}", k["tool"], "05 Report"))
    if k.get("illustrative"):
        meta += '<span class="ill">Illustrative</span>'
    status = (record.get("landed") or {}).get("status")
    status_html = f'<span class="st {e(status)}">{e(status)}</span>' if status in ("landed", "watch", "stalled") else '<span class="mono t3">not read</span>'
    lede = (
        f"{n['questions']} questions a board will likely ask about this bet. {n['answered']} are answered from the loop record, each figure with its source. "
        f"{n['open']} are open, each with an owner to chase before the meeting."
    )
    facts = (
        f'<div class="facts"><span><b>{n["questions"]}</b>Questions</span><span><b>{n["answered"]}</b>Answered</span>'
        f"<span><b>{n['open']}</b>Open</span><span>{status_html}Bet status, from did-it-land</span></div>"
    )
    first = "".join(row(qs[i]) for i in k["first"])
    opens_q = [q for q in k["questions"] if q["check"] == "open" and q["id"] not in k["first"]]
    answered_q = [q for q in k["questions"] if q["check"] == "answered" and q["id"] not in k["first"]]
    opens = "".join(row(q) for q in opens_q)
    answered = "".join(row(q) for q in answered_q)
    keys = []
    for key in k["read"]:
        tool, as_of = written_by(record, key)
        keys.append(f"<tr><td>{e(key)}</td><td>{e(tool)}</td><td class='mo'>{e(as_of)}</td><td>read</td></tr>")
    for key in k["not_in_record"]:
        keys.append(f"<tr><td>{e(key)}</td><td>{e(WRITER_LABEL[key])}</td><td class='mo'></td><td class='t3'>not in the record yet</td></tr>")
    brief = k["brief"]
    brief_line = f"Brief {brief['path']}: " + ("complete" if brief["complete"] else "cannot be used") + (", unchanged since the record opened." if brief["unchanged"] else ".")
    ledger = "".join(
        f"<tr id='{e(fid)}'><td class='mo'>{e(fid)}</td><td class='num'>{e(_shown(f))}</td><td>{e(f['source'])}</td>"
        f"<td class='mo'>{e(_window(f['window']))}</td><td class='mo'>{e(str(f['as_of'])[:10])}</td></tr>"
        for fid, f in k["figures"].items()
    )

    def section(label: str, heading: str, body: str, lede_text: str = "") -> str:
        if not body:
            return ""
        lt = f'<p class="lede">{e(lede_text)}</p>' if lede_text else ""
        return f'<section class="slide"><div class="meta"><span>{e(label)}</span></div><h2>{e(heading)}</h2>{lt}{body}</section>'

    def fold(heading: str, body: str) -> str:
        return f'<details class="more"><summary>{e(heading)}</summary>{body}</details>' if body else ""

    summary = "".join(f"<li><b>{e(i)}</b>{e(line)}</li>" for i, line in summary_lines(k))
    folds = (
        fold(f"Open, with an owner ({len(opens_q)})", f'<div class="qa">{opens}</div>' if opens else "")
        + fold(f"Answered from the record ({len(answered_q)})", f'<div class="qa">{answered}</div>' if answered else "")
        + fold(
            "What the record holds",
            f'<div class="tablewrap keys"><table><thead><tr><th>Key</th><th>Written by</th><th>As of</th><th>Here</th></tr></thead><tbody>{"".join(keys)}</tbody></table></div>'
            f'<p class="sub">{e(brief_line)}</p>',
        )
        + fold(
            f"Every figure, with its source ({len(k['figures'])})",
            f'<div class="tablewrap"><table><thead><tr><th>ID</th><th class="num">Figure</th><th>Source</th><th>Window</th><th>As of</th></tr></thead><tbody>{ledger}</tbody></table></div>',
        )
    )

    return (
        '<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{e(title)}</title><style>{stylesheet()}{PAGE_CSS}</style></head><body><main class="solo">'
        f'<section class="slide cover"><div class="brand">{MARK}<span translate="no">DACARD</span></div><div class="meta">{meta}</div>'
        f'<h1>{e(title)}</h1><p class="answer">{e(answer_line(k))}</p><ul class="sum">{summary}</ul>{facts}</section>'
        + section(
            "Prepare first",
            "The five to prepare first",
            f'<div class="qa">{first}</div>',
            "Ranked in code: the result and the decision weigh most, an open question weighs more, and a question the board asked last time most of all.",
        )
        + section("More", "The rest, folded", folds, lede)
        + '<p class="foot">Every answer quotes a figure the loop record holds, with its source; code checks each one. '
        "An answer says what moved and when, not why. Landed, watch or stalled is did-it-land's call, printed as it set it.</p></main></body></html>\n"
    )


def _window(w: dict[str, Any]) -> str:
    """2026-11-01 to 2026-11-14; one date when from and to agree; "by" a date when there is no start."""
    a, b = w.get("from"), w.get("to")
    if a and b:
        return a if a == b else f"{a} to {b}"
    return f"by {b}" if b else (f"from {a}" if a else "")


def _shown(f: dict[str, Any]) -> str:
    """A ledger row's figure with its unit: 43%, $0.0338 per task, 25% over budget, 10,300 tokens per task."""
    unit, value = str(f.get("unit") or ""), num(f)
    low = unit.lower()
    if low.startswith("%") or low == "$":
        return value + unit[1:]
    if low.startswith("share"):
        return f"{value} {unit[6:]}".strip()
    if low.startswith("usd"):
        return f"{value}{unit[3:]}"
    return value if low in ("number", "") else f"{value} {unit}"


def markdown(record: dict[str, Any]) -> str:
    """The plain-text twin of the page."""
    k = record["board_qa"]
    n = {name: f["value"] for name, f in k["counts"].items()}
    status = (record.get("landed") or {}).get("status") or "not read"
    lines = [f"# Board questions: {k['bet_title']}", ""]
    lines.append(f"As of {k['as_of']}. {k['tool']}. Step 05 Report." + (" Illustrative: every figure is invented." if k.get("illustrative") else ""))
    lines += ["", f"**{answer_line(k)}**", ""]
    lines += [f"- {i}. {line}" for i, line in summary_lines(k)]
    lines += ["", f"{n['questions']} questions: {n['answered']} answered from the record, {n['open']} open with an owner. Bet status, from did-it-land: {status}.", ""]

    def item(q: dict[str, Any]) -> list[str]:
        out = [f"**{q['id']}. {q['question']}** ({q['check']})", ""]
        if q.get("asked_last_time"):
            out += ["_Asked at the last meeting._", ""]
        if q["check"] == "answered":
            out.append(str(q.get("answer")) + (f" Stated by {q['stated_by']}." if q.get("stated_by") else ""))
        else:
            out.append(f"{q['missing']} Owner: {q['owner']}. Due: {q['due']}.")
        return [*out, ""]

    qs = {q["id"]: q for q in k["questions"]}
    lines += ["## Prepare these first", ""]
    for i in k["first"]:
        lines += item(qs[i])
    rest_open = [q for q in k["questions"] if q["check"] == "open" and q["id"] not in k["first"]]
    rest_ans = [q for q in k["questions"] if q["check"] == "answered" and q["id"] not in k["first"]]
    lines += ["<details>", "<summary>The rest: open and answered questions, and every figure with its source</summary>", ""]
    if rest_open:
        lines += ["## Open, with an owner", ""]
        for q in rest_open:
            lines += item(q)
    if rest_ans:
        lines += ["## Answered from the record", ""]
        for q in rest_ans:
            lines += item(q)
    lines += ["## Ledger", "", "| ID | Figure | Source | Window | As of |", "|---|---|---|---|---|"]
    for fid, f in k["figures"].items():
        w = f["window"]
        lines.append(f"| {fid} | {_shown(f)} | {str(f['source']).replace('|', '/')} | {_window(w)} | {str(f['as_of'])[:10]} |")
    lines += ["", "Not in the record yet: " + (", ".join(k["not_in_record"]) or "nothing") + ".", "", "</details>"]
    return "\n".join(lines) + "\n"
