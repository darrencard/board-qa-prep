"""The board_qa key as one self-contained HTML page, in the Leader Report style guide and the Landing Loop's one
visual family, and its Markdown twin.

The page takes the report's whole stylesheet from its template (assets/vendor/template.html, vendored
byte-identical at a pinned commit) and draws its picture with svgkit (scripts/vendor/svgkit.py, vendored
byte-identical from landing-loop). Only a few rules for this page's layout are added.

It reads top down for someone who has never seen the loop: the shared header, the verdict as the heading, the
project's status as did-it-land set it, then the picture as scorecard rows (svgkit 1.2.0): a share bar first (13 of
15 answered), then one row per likely question, open first with its due date and its owner in brass, then the
answered ones with the steps of the project file each reads. Geist Mono 12px for labels and figures, Geist 14px for
names, no text inside a picture, no box inside the frame. One next step follows: the first open question, owned by
its person. The five to prepare first lead the detail, each with its point in one line and the long answer folded;
the other questions, the figures with their sources and the project file's key fold away. Public copy uses plain
words: project, target, the likely range, too close to call, the large model. Cited check words print in their
skill's words: eval-kit's "not confirmed: too close to call", did-it-land's "inside normal ups and downs".

Green, grey-white and red mean a project's status only, and appear once, on the status did-it-land set. Brass marks
a person's call: an open question's owner and due date. Check words, answered and open alike, are text, never boxed
chips: open in ink, answered muted. The picture draws only figures the page prints, and its aria-label states the
answer.

Nothing is loaded from the network, nothing depends on the clock or the machine, and every piece of text from
the record is escaped.

Standard library only. Python 3.11 or later.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import svgkit as sk  # noqa: E402  (vendored, unchanged; see VENDORED.json)
from display import num  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "vendor" / "template.html"
STYLE = re.compile(r"<style>(.*?)</style>", re.S)
CITE = re.compile(r"\s*\[(F\d{1,3})\]")

# Layout for this page only. Everything else comes from the template's stylesheet and svgkit.CSS.
# In the scorecard, a row with no picture gives its name the picture column too, so names stay on one line; the
# figure column prints in one case, numerals and capitals, as /update does; and the answered questions fold into a
# <details> whose rows keep the frame's columns (subgrid through ::details-content).
PAGE_CSS = """
main.solo{margin-left:0}
.solo .slide{min-height:0}
.solo .slide.cover{min-height:0;padding-top:40px;padding-bottom:48px;justify-content:flex-start}
.solo h1{font-size:clamp(34px,4.6vw,60px);line-height:1;letter-spacing:-.04em;max-width:22ch;margin-bottom:20px}
.solo .lede{margin-bottom:24px}
.solo .lede b{color:var(--t1);font-weight:500}
.marks{display:flex;flex-wrap:wrap;align-items:center;gap:10px 28px;margin:0 0 20px;font:400 11px/16px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}
.marks>span{display:inline-flex;align-items:center;gap:10px}
.next{margin-top:28px;display:grid;grid-template-columns:200px minmax(0,1fr);gap:8px 32px;align-items:baseline;border:1px solid var(--brass);border-radius:12px;padding:20px 24px;background:var(--brass-bg)}
.next>b{font:400 11px/22px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--brass)}
.next p{margin:0;font-size:16px;line-height:1.5;color:var(--t1)}
.next .who{display:flex;flex-wrap:wrap;gap:4px 24px;margin-top:10px;font:400 11.5px/16px var(--mono);color:var(--brass)}
.next .who span::before{font-size:11px;letter-spacing:.1em;color:var(--t3);margin-right:8px}
.next .who .o::before{content:"OWNER"}.next .who .d::before{content:"DUE"}
.cols{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:24px 56px;align-items:start}
.cols h3{margin-bottom:8px}
.qa>div{display:grid;grid-template-columns:44px minmax(0,1fr) auto;gap:4px 16px;border-top:1px solid var(--line);padding:14px 0}
.qa .id{font:400 11px/22px var(--mono);letter-spacing:.1em;color:var(--t3)}
.qa .q{display:block;color:var(--t1);font-size:15px;line-height:1.45}
.qa .a{display:block;color:var(--t2);font-size:13.5px;line-height:1.55;margin-top:6px;max-width:72ch}
.qa .k{display:block;font:400 11px/16px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--t3);margin-top:8px}
.qa details{margin-top:6px}
.qa details>summary{cursor:pointer;font:400 11px/18px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}
.qa details>summary:hover{color:var(--t1)}
.qa details .a{margin-top:4px}
.wd{font:400 12px/16px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--t3);white-space:nowrap}
.wd.open{color:var(--t1)}
.own{display:block;font:400 11.5px/18px var(--mono);color:var(--brass);margin-top:8px}
.own i{font-style:normal;font-size:11px;letter-spacing:.1em;color:var(--t3);margin-right:6px}
.own i+i{margin-left:18px}
.rest{margin:0;padding:0;list-style:none}
.rest li{display:grid;grid-template-columns:40px minmax(0,1fr) auto;gap:4px 12px;align-items:baseline;border-top:1px solid var(--line);padding:9px 0;font-size:13.5px;line-height:1.45;color:var(--t2)}
.rest li b{font:400 11px/18px var(--mono);letter-spacing:.1em;color:var(--t3);font-weight:400}
.rest a{color:inherit;text-decoration:none}
.rest a:hover{color:var(--t1)}
.solo details.more{border-top:1px solid var(--line);padding:14px 0;margin:0}
.more>summary{cursor:pointer;font:400 11px/20px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t2)}
.more>summary:hover{color:var(--t1)}
.more[open]>summary{margin-bottom:8px}
.more p{font-size:13px;color:var(--t2);max-width:80ch}
.tablewrap td,.tablewrap th{overflow-wrap:anywhere}
::selection{background:var(--t1);color:var(--bg)}
:focus-visible{outline-color:var(--t1)}
.foot{max-width:1120px;margin:0 auto;padding:28px 40px 64px;color:var(--t3);font-size:12px}
@media (max-width:980px){.foot{padding:24px 16px 48px}.solo .slide.cover{padding-top:24px}.cols,.next{grid-template-columns:1fr}
.qa>div{grid-template-columns:36px minmax(0,1fr)}.qa .w{grid-column:2}
.stack table,.stack tbody,.stack tr,.stack td{display:block}.stack tr:first-child{display:none}.stack tr{padding:10px 16px;border-bottom:1px solid var(--line)}
.stack td{border:0;padding:3px 0;display:grid;grid-template-columns:96px 1fr;gap:12px}.stack td.num{text-align:left;white-space:normal}
.stack td::before{content:attr(data-l);font:400 11px/20px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}}
.scg .sc-l{text-transform:uppercase;letter-spacing:.06em}
@container sc (min-width:800px){.scg .sc-r:has(>.sc-p:empty)>.sc-n{grid-column:1/3}.scg .sc-r:has(>.sc-p:empty)>.sc-p{display:none}}
.scg .sc-d,.scg .sc-d::details-content{grid-column:1/-1;display:grid;grid-template-columns:subgrid}
.scg .sc-d{margin:0;padding:0;border:0}.scg .sc-d>summary{margin:0;cursor:pointer}.scg .sc-d>summary:hover{color:var(--t1)}
@container sc (max-width:799.98px){.scg .sc-d,.scg .sc-d::details-content{display:block}}
"""

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
# The smallest text the page prints, at every width. The vendored template and svgkit keep their own sizes on disk
# (both are hash-pinned); the page raises any smaller size to this one as it inlines their rules.
FONT_FLOOR = 11
FONT_SIZE = re.compile(r"(font-size:\s*|font:[^;{}]*?)(\d+(?:\.\d+)?)px")


def floor_fonts(css: str) -> str:
    """Every font size below FONT_FLOOR, raised to it: font-size and the size in a font shorthand."""
    return FONT_SIZE.sub(lambda m: m.group(1) + (str(FONT_FLOOR) if float(m.group(2)) < FONT_FLOOR else m.group(2)) + "px", css)


NUMBER_WORDS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve")

# The record's answers in the page's words. The record keeps its words; the check reads those, not these.
WORDS = (
    (r"\bvendor-[a-z0-9]+/xl\b", "the large model"),
    (r"\bThe record\b", "The project file"),
    (r"\b(?<![\w-])record(?![\w-])", "project file"),
    (r"\bFrom decision-record, as of\b", "As of"),
    (r"(^|\. )bet-portfolio-review\b", r"\1The portfolio review"),
    (r"\bbet-portfolio-review\b", "the portfolio review"),
    (r"\bcontext limit\b", "length limit"),
    (r"\bThe bar:", "The target:"),
    (r"\ba bar of\b", "a target of"),
    (r"(?<![\w-])bar(?![\w-])", "target"),
    (r"\bWhat did we bet on\b", "What did we set out to do"),
    (r"(?<![\w-])bets(?![\w-])", "projects"),
    (r"(?<![\w-])bet(?![\w-])", "project"),
    (r"(^|\. )v(\d+(?:\.\d+)+)('s)? held-out pass rate\b", r"\1Version \2\3 pass rate on test cases kept back"),
    (r"\bHeld-out pass rate\b", "Pass rate on test cases kept back"),
    (r"\bheld-out pass rate\b", "pass rate on test cases kept back"),
    (r"(^|\. )v(\d+(?:\.\d+)+)\b", r"\1Version \2"),
    (r"\bv(\d+(?:\.\d+)+)\b", r"version \1"),
    (r"\bthe 95% interval\b", "the likely range"),
    (r"\b95% interval\b", "likely range"),
    (r"\binside (?:the )?noise\b", "too close to call"),
    (r"\beval-kit's build check\b", "The quality test"),
    (r"\bthe cost-budget-check result\b", "the cost check's result"),
    (r"\bthe eval-kit result\b", "the quality test's result"),
    (r"(^|\. )eval-kit\b", r"\1The quality test"),
    (r"\beval-kit\b", "the quality test"),
    (r"(^|\. )cost-budget-check\b", r"\1The cost check"),
    (r"\bcost-budget-check\b", "the cost check"),
    (r"\bTokens per task:", "AI usage per task:"),
    (r"\bPrice per token:", "AI price per unit:"),
    (r"\bThe postmortem\b", "The after-action review"),
    (r"\bthe postmortem\b", "the after-action review"),
    (r"\brollback trigger\b", "undo trigger"),
    (r"\brollback\b", "undo plan"),
    (r"\beval-plan\b", "quality test plan"),
    (r"\bno holdout group\b", "no comparison group held back"),
    (r"\bspreads above that mean\b", "times that spread above the average"),
    (r"\bThe outcome series\b", "The result it should drive"),
    (r"\bthe metric\b", "the number"),
    (r"\bThe point estimate\b", "The rate itself"),
    (r"\bFlags on the read: over-cost-budget\.", "The read also flags that cost is over budget."),
    (r"\bread hold under a waiver from (.+?) until\b", r"failed its check and shipped on the OK of \1, until"),
    (r"\bwaived by (.+?) until\b", r"shipped on the OK of \1, until"),
    (r"^Was the waived check closed before its waiver ran out\?$", "A failed check shipped on a named person's OK. Was it closed before that OK ran out?"),
    (r"\bthe waived check\b", "the check that shipped on a named person's OK"),
    (r"\bits waiver ran out\b", "that OK ran out"),
)


def e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def plain(text: str) -> str:
    for pattern, to in WORDS:
        text = re.sub(pattern, to, text)
    return text


def stylesheet() -> str:
    try:
        found = STYLE.search(TEMPLATE.read_text(encoding="utf-8"))
    except OSError:
        found = None
    return found.group(1) if found else ""


def count_word(n: int) -> str:
    return NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)


def cites(text: str) -> str:
    """Escaped text with each [F01] drawn as the report's ledger tag."""
    out, last = [], 0
    for m in CITE.finditer(text):
        out.append(e(text[last : m.start()]))
        out.append(f'<a class="led" href="#{e(m.group(1))}">{e(m.group(1))}</a>')
        last = m.end()
    out.append(e(text[last:]))
    return "".join(out)


def first_sentence(text: str) -> tuple[str, str]:
    """The point, and the rest. A sentence ends at a full stop before a space and a capital letter or a digit."""
    m = re.search(r"\.\s+(?=[A-Z0-9$])", text)
    return (text, "") if not m else (text[: m.start() + 1], text[m.end() :])


def written_by(record: dict[str, Any], key: str) -> tuple[str, str]:
    """(tool and version, as_of) a key says it was written by, as it says it."""
    k = record.get(key) or {}
    tool = k.get("tool") or k.get("computed_by") or " ".join(str(x) for x in (k.get("skill"), k.get("skill_version") or k.get("version")) if x) or WRITER_LABEL[key]
    if key == "spec" and k.get("version") and str(k.get("version")) not in str(tool):
        tool = f"{tool} {k['version']}"
    return str(tool), str(k.get("as_of") or "")[:10]


def answer_line(k: dict[str, Any]) -> str:
    """The verdict: how many of the likely questions the record answers, and how many need a person."""
    n = {name: f["value"] for name, f in k["counts"].items()}
    if not n["open"]:
        return f"The project file answers all {n['questions']} likely board questions."
    need = "needs an owner's answer" if n["open"] == 1 else "need an owner's answer"
    return f"The project file answers {n['answered']} of {n['questions']} likely board questions. {count_word(n['open'])} {need} before the meeting."


def lede(k: dict[str, Any]) -> str:
    return (
        f"{e(k['bet_title'])} is a project you expect to move a number. Its <b>landing brief</b>, a one-page plan, sets what good looks like, "
        "by when and at what cost. As the project moves from plan to board, each step adds its page to the project file. These are the questions "
        "a board will likely ask, each answered from that file with its source, or left open with a named owner. Code checks every figure."
    )


# The signature picture: scorecard rows (svgkit 1.2.0)

# Each answered question's topic in one or two words, so the rows stay short; the full question is in the detail.
# Unknown topics print as they are.
TOPIC = {
    "brief": "The plan",
    "landed": "Did it land",
    "noise": "Real or noise",
    "outcome": "The result",
    "decision-made": "Decisions",
    "decision-open": "Open calls",
    "quality": "Quality",
    "eval-gain": "New version",
    "cost": "Cost",
    "cost-owner": "Cost owner",
    "release": "Release",
    "signals": "Customers",
    "postmortem": "Fixes",
    "portfolio": "Why this one",
    "past": "Last meeting",
}

# Where an answer comes from, in plain words: the step that wrote the key it reads.
SOURCE = {
    "brief": "landing brief",
    "portfolio": "portfolio review",
    "decisions": "decisions",
    "spec": "build plan check",
    "release": "release readiness",
    "cost": "cost check",
    "evals": "quality test",
    "landed": "did it land",
    "signals": "customer signals",
    "postmortem": "after-action review",
}


def source_line(q: dict[str, Any]) -> str:
    """The steps an answer reads, as the figure: `DID IT LAND`, `COST CHECK · AFTER-ACTION REVIEW`."""
    return " · ".join(SOURCE.get(x, x) for x in q.get("from_keys") or []).upper() or "THE PROJECT FILE"


def team_of(owners: list[str]) -> str:
    """The team every owner shares ("Lead, Quoting squad" and "Head of Product, Quoting squad" share "Quoting squad"),
    or "" when they do not all name the same one. The frame prints it once in its head; each row prints the role."""
    teams = {o.rpartition(", ")[2] for o in owners if ", " in o}
    if len(owners) < 2 or len(teams) != 1 or any(", " not in o for o in owners):
        return ""
    return teams.pop()


def role_of(owner: str, team: str) -> str:
    return owner[: -len(", " + team)] if team and owner.endswith(", " + team) else owner


def rows(k: dict[str, Any]) -> str:
    """A share bar first (answered of all), then one row per question, open first: the question, its due date and
    its owner in brass; then the answered ones by topic, with the steps they read from. Check words are text, never
    chips."""
    n = {name: f["value"] for name, f in k["counts"].items()}
    out = [
        sk.sc_row(
            "Answered from the project file",
            picture=sk.share_bar(n["answered"], n["questions"]),
            figure=sk.figure_line(f"{n['answered']} of {n['questions']}"),
            word=sk.check_word(f"{n['open']} open", ink=True) if n["open"] else sk.check_word("none open"),
        )
    ]
    opens = [q for q in k["questions"] if q["check"] == "open"]
    done = [q for q in k["questions"] if q["check"] != "open"]
    team = team_of([q["owner"] for q in opens])
    for q in opens:
        out.append(
            sk.sc_row(
                f"{q['id']}. {plain(q['question'])}",
                figure=sk.figure_line(str(q["due"]).upper()),
                word=sk.check_word("open", ink=True) + sk.person_call(role_of(q["owner"], team)),
            )
        )
    answered = [sk.sc_row(f"{q['id']}. {TOPIC.get(q['topic'], q['topic'])}", figure=sk.figure_line(source_line(q)), word=sk.check_word("answered")) for q in done]
    if answered:
        out.append(f'<details class="sc-d"><summary class="sc-x">The {len(done)} answered, with the steps each answer reads</summary>{"".join(answered)}</details>')
    legend = f"<span>{n['answered']} of {n['questions']} answered</span>"
    if team:
        legend += f'<span class="sc-k">{sk.person_mark()}{e(team)}</span>'
    return sk.sc_frame(
        out,
        label=answer_line(k),
        title="Likely board questions",
        head=["Question", "", "Due · read from", "Check"],
        legend=legend,
        caption=(
            f"One row per likely question, {n['questions']} in all: open first, each owner's role in brass"
            + (f" (every owner is in {team}, named once in the head)" if team else "")
            + "; then answered, folded, by topic, with the steps each answer reads."
        ),
        illustrative=bool(k.get("illustrative")),
    )


# The rows


def row(q: dict[str, Any], short: bool = False) -> str:
    """One question. Short: the point in one line, the rest of the answer folded."""
    body = plain(str((q.get("answer") if q["check"] == "answered" else q.get("missing")) or ""))
    extra = ""
    if q["check"] == "open":
        extra = f'<span class="own"><i>OWNER</i>{e(q["owner"])}<i>DUE</i>{e(q["due"])}</span>'
    elif q.get("stated_by"):
        extra = f'<span class="k">Stated by {e(q["stated_by"])}</span>'
    asked = '<span class="k">Asked at the last meeting</span>' if q.get("asked_last_time") else ""
    if short:
        point, more = first_sentence(body)
        text = f'<span class="a">{cites(point)}</span>'
        if more:
            text += f'<details><summary>The full answer, with sources</summary><span class="a">{cites(more)}</span></details>'
    else:
        text = f'<span class="a">{cites(body)}</span>'
    return (
        f'<div id="{e(q["id"])}"><span class="id">{e(q["id"])}</span>'
        f'<span><span class="q">{e(plain(q["question"]))}</span>{text}{extra}{asked}</span>'
        f'<span class="w"><span class="wd {e(q["check"])}">{e(q["check"])}</span></span></div>'
    )


def summary_lines(k: dict[str, Any]) -> list[tuple[str, str]]:
    """One line per question to prepare first: (id, the question and where it stands)."""
    qs = {q["id"]: q for q in k["questions"]}
    out = []
    for i in k["first"]:
        q = qs[i]
        where = f"open, owner {q['owner']}, due {q['due']}" if q["check"] == "open" else "answered from the project file"
        if q["check"] == "answered" and q.get("stated_by"):
            where = f"answered, stated by {q['stated_by']}"
        out.append((i, f"{plain(q['question'])} ({where})"))
    return out


class Table:
    """A table whose cells carry their column name, so a phone shows each row as labelled lines."""

    def __init__(self, heads: tuple[str, ...]) -> None:
        self.heads = heads
        self.rows: list[str] = []

    def row(self, *cells: tuple[str, str], row_id: str = "") -> None:
        tds = []
        for head, (cls, body) in zip(self.heads, cells, strict=True):
            attr = f' class="{cls}"' if cls else ""
            tds.append(f'<td{attr} data-l="{e(head)}">{body}</td>')
        rid = f' id="{e(row_id)}"' if row_id else ""
        self.rows.append(f"<tr{rid}>" + "".join(tds) + "</tr>")

    def html(self) -> str:
        head = "<tr>" + "".join(f"<th>{e(h)}</th>" for h in self.heads) + "</tr>"
        return f'<div class="tablewrap stack"><table>{head}{"".join(self.rows)}</table></div>'


def fold(heading: str, body: str) -> str:
    return f'<details class="more"><summary>{e(heading)}</summary>{body}</details>' if body else ""


def page(record: dict[str, Any]) -> str:
    k = record["board_qa"]
    qs = {q["id"]: q for q in k["questions"]}
    n = {name: f["value"] for name, f in k["counts"].items()}
    ill = bool(k.get("illustrative"))
    title = f"Board questions: {k['bet_title']}"
    header = sk.page_header("Board Q&A prep", date=f"As of {k['as_of']}", version="v" + k["tool"].rsplit(" ", 1)[-1], illustrative=ill)
    status = (record.get("landed") or {}).get("status")
    status_html = f'<span class="st {e(status)}">{e(status)}</span>' if status in ("landed", "watch", "stalled") else '<span class="mono t3">not read</span>'
    marks = f'<p class="marks"><span>Project status, from did-it-land {status_html}</span><span>{n["answered"]} answered</span><span>{n["open"]} open</span></p>'
    lead = next((qs[i] for i in k["first"] if qs[i]["check"] == "open"), None)
    step = ""
    if lead:
        step = (
            f'<div class="next"><b>What to do next</b><div><p>Get an answer to {e(lead["id"])}, &ldquo;{e(plain(lead["question"]))}&rdquo;, '
            f'from its owner before the meeting.</p><span class="who"><span class="o">{e(lead["owner"])}</span><span class="d">{e(lead["due"])}</span></span></div></div>'
        )
    cover = f'<section class="slide cover">{header}<h1>{e(answer_line(k))}</h1><p class="lede">{lede(k)}</p>{marks}{rows(k)}{step}</section>'

    first = "".join(row(qs[i], short=True) for i in k["first"])
    rest = [q for q in k["questions"] if q["id"] not in k["first"]]
    others = "".join(f'<li><b>{e(q["id"])}</b><a href="#{e(q["id"])}">{e(plain(q["question"]))}</a><span class="wd {e(q["check"])}">{e(q["check"])}</span></li>' for q in rest)
    detail = (
        '<section class="slide"><div class="meta"><span>Prepare first</span></div><div class="cols">'
        f'<div><h3>The five to prepare first</h3><div class="qa">{first}</div></div>'
        f'<div><h3>The other {len(rest)}</h3><ul class="rest">{others}</ul></div></div></section>'
    )

    keys = Table(("Key", "Written by", "As of", "Here"))
    for key in k["read"]:
        tool, as_of = written_by(record, key)
        keys.row(("mo", e(key)), ("", e(tool)), ("mo", e(as_of)), ("", "read"))
    for key in k["not_in_record"]:
        keys.row(("mo", e(key)), ("", e(WRITER_LABEL[key])), ("mo", ""), ("t3", "not in the project file yet"))
    brief = k["brief"]
    brief_line = (
        f"Landing brief {brief['path']}: " + ("complete" if brief["complete"] else "cannot be used") + (", unchanged since the record opened." if brief["unchanged"] else ".")
    )
    ledger = Table(("ID", "Figure", "Source", "Window", "As of"))
    for fid, f in k["figures"].items():
        ledger.row(("mo", e(fid)), ("num", e(_shown(f))), ("", e(f["source"])), ("mo", e(_window(f["window"]))), ("mo", e(str(f["as_of"])[:10])), row_id=fid)
    rest_rows = "".join(row(q) for q in rest)
    engineers = (
        f"<p>Skill: <code>board-qa-prep</code> {e(k['tool'].rsplit(' ', 1)[-1])}.</p>{keys.html()}<p>{e(brief_line)}</p>{ledger.html()}"
        "<p>The answers above print the record's words in plain words; the record keeps them as written, and the check reads those. "
        "board_qa.py adds its page to the project file: the <code>board_qa</code> key of <code>landing/&lt;bet&gt;.json</code>, and no other key.</p>"
    )
    more = (
        '<section class="slide"><div class="meta"><span>Detail</span></div>'
        + fold(f"The other {len(rest)} questions, answered or open", f'<div class="qa">{rest_rows}</div>' if rest_rows else "")
        + fold("For your engineers", engineers)
        + "</section>"
    )
    return (
        '<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{e(title)}</title><style>{floor_fonts(stylesheet() + sk.CSS + sk.SCORECARD_CSS + PAGE_CSS)}</style></head><body><main class="solo">'
        f"{cover}{detail}{more}"
        '<p class="foot">Every answer quotes a figure the project file holds, with its source; code checks each one. '
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
    """The plain-text twin of the page: the same words, in the same order, with the long text folded."""
    k = record["board_qa"]
    n = {name: f["value"] for name, f in k["counts"].items()}
    qs = {q["id"]: q for q in k["questions"]}
    status = (record.get("landed") or {}).get("status") or "not read"
    lines = [f"# {answer_line(k)}", ""]
    lines.append(f"Board Q&A prep v{k['tool'].rsplit(' ', 1)[-1]}. As of {k['as_of']}." + (" Illustrative: every figure is invented." if k.get("illustrative") else ""))
    lines += ["", re.sub(r"</?b>", "", html.unescape(lede(k))), ""]
    lines += [f"**Project status, from did-it-land:** {status}. {n['answered']} answered, {n['open']} open.", ""]
    lead = next((qs[i] for i in k["first"] if qs[i]["check"] == "open"), None)
    if lead:
        lines += [
            "## What to do next",
            "",
            f'Get an answer to {lead["id"]}, "{plain(lead["question"])}", from its owner before the meeting. Owner: {lead["owner"]}. Due: {lead["due"]}.',
            "",
        ]

    def item(q: dict[str, Any], short: bool) -> list[str]:
        out = [f"**{q['id']}. {plain(q['question'])}** ({q['check']})", ""]
        if q.get("asked_last_time"):
            out += ["_Asked at the last meeting._", ""]
        body = plain(str((q.get("answer") if q["check"] == "answered" else q.get("missing")) or ""))
        point, rest = first_sentence(body) if short else (body, "")
        tail = f" Stated by {q['stated_by']}." if q["check"] == "answered" and q.get("stated_by") else ""
        if q["check"] == "open":
            tail = f" Owner: {q['owner']}. Due: {q['due']}."
        out.append(point + ("" if rest else tail))
        if rest:
            out += ["", "<details>", "<summary>The full answer, with sources</summary>", "", rest + tail, "", "</details>"]
        return [*out, ""]

    lines += ["## The five to prepare first", ""]
    for i in k["first"]:
        lines += item(qs[i], short=True)
    rest = [q for q in k["questions"] if q["id"] not in k["first"]]
    lines += [f"## The other {len(rest)}", ""]
    lines += [f"- {q['id']}. {plain(q['question'])} ({q['check']})" for q in rest]
    lines += ["", "<details>", f"<summary>The other {len(rest)} questions, answered or open</summary>", ""]
    for q in rest:
        lines += item(q, short=False)
    lines += ["</details>", "", "<details>", "<summary>For your engineers</summary>", ""]
    lines += [f"Skill: `board-qa-prep` {k['tool'].rsplit(' ', 1)[-1]}.", ""]
    lines += ["| ID | Figure | Source | Window | As of |", "|---|---|---|---|---|"]
    for fid, f in k["figures"].items():
        lines.append(f"| {fid} | {_shown(f)} | {str(f['source']).replace('|', '/')} | {_window(f['window'])} | {str(f['as_of'])[:10]} |")
    lines += ["", "Read: " + (", ".join(k["read"]) or "nothing") + ". Not in the record yet: " + (", ".join(k["not_in_record"]) or "nothing") + ".", ""]
    lines += ["board_qa.py adds its page to the project file: the `board_qa` key of `landing/<bet>.json`, and no other key.", "", "</details>"]
    return "\n".join(lines) + "\n"
