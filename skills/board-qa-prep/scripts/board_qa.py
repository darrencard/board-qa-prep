#!/usr/bin/env python3
"""Board Q&A prep from the Landing Loop record: the questions a board will likely ask about one bet.

Reads landing/<bet>.json (any of the keys portfolio, decisions, spec, release, cost, evals, landed, signals,
postmortem) and the bet's landing brief, and writes only the `board_qa` key. Each question is either
answered, quoting the record's own figures with their sources, or open, with an owner and a due date.
Code drafts every question, answer and figure; the model may reword the text, and the check blocks any
figure or status word the record does not hold.

Usage:
  python3 board_qa.py prep  landing/<bet>.json [--past past-questions.md] [--owner NAME] [--due TEXT]
                            [--as-of YYYY-MM-DD] [--html page.html] [--md page.md]
  python3 board_qa.py check landing/<bet>.json                 # check the board_qa key; exit 1 on any error
  python3 board_qa.py edit  landing/<bet>.json Q03 --question TEXT --answer TEXT
  python3 board_qa.py close landing/<bet>.json Q05 --text TEXT --by NAME
  python3 board_qa.py render landing/<bet>.json --html page.html [--md page.md]

`edit` and `close` save only when the check passes. `close` records a stated answer: words a named
person gave, with no figure the record does not hold.

Standard library only. Python 3.11 or later. No network calls.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import io
import re
import sys
from pathlib import Path
from typing import Any

if sys.version_info < (3, 11):  # noqa: UP036  (the message is the point: macOS python3 is often 3.9)
    sys.exit("board-qa-prep needs Python 3.11 or later. Run it with python3.11, python3.12 or newer.")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check  # noqa: E402
import landing_brief  # noqa: E402
import loop  # noqa: E402
import render_html  # noqa: E402
from display import num, sig  # noqa: E402

VERSION = "0.3.0"
TOOL = f"board-qa-prep {VERSION}"
DEFAULT_DUE = "before the board meeting"
MAX_PAST_BYTES = 200_000

# Topic weights for "Prepare these first": what a board weighs most. A default judgment, not a measure.
WEIGHT = {
    "landed": 3,
    "decision": 3,
    "cost": 2,
    "cost-owner": 2,
    "quality": 2,
    "noise": 2,
    "spec": 2,
    "release": 2,
    "postmortem": 2,
    "past": 2,
    "brief": 1,
    "outcome": 2,
    "eval-gain": 1,
    "signals": 1,
    "portfolio": 1,
}
# Words that place a question asked at the last meeting on a topic. Word overlap, nothing cleverer.
TOPIC_WORDS = {
    "landed": {"land", "landed", "working", "work", "using", "used", "adoption", "accepted", "acceptance", "metric", "result"},
    "outcome": {"jobs", "win", "wins", "won", "revenue", "outcome", "customers", "business"},
    "cost": {"cost", "costs", "spend", "budget", "price", "money", "expensive", "margin", "per"},
    "quality": {"quality", "accurate", "accuracy", "errors", "wrong", "eval", "evals", "trust", "autonomy"},
    "decision": {"scale", "next", "decide", "decision", "invest", "stop", "continue", "expand"},
    "spec": {"spec", "rollback", "plan", "prd"},
    "release": {"release", "ship", "shipped", "ready", "launch"},
    "signals": {"customers", "feedback", "complaints", "saying", "signal"},
    "postmortem": {"incident", "outage", "postmortem", "fix", "fixes", "broke"},
    "portfolio": {"why", "priority", "prioritise", "others", "portfolio", "rank"},
}
STOP = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "we",
    "our",
    "it",
    "of",
    "to",
    "do",
    "does",
    "did",
    "and",
    "or",
    "for",
    "on",
    "in",
    "this",
    "that",
    "what",
    "how",
    "when",
    "will",
    "us",
    "any",
    "be",
}


class PrepError(ValueError):
    """Input that cannot be used. Nothing is written when this is raised."""


# --- figures -------------------------------------------------------------------------------------


class Ledger:
    """The figures the answers cite, F01 upward, each copied from the record with a pointer to where it came from."""

    def __init__(self, record: dict[str, Any]):
        self.record = record
        self.rows: dict[str, dict[str, Any]] = {}
        self.by_path: dict[str, str] = {}

    def add(self, f: dict[str, Any], path: str) -> str:
        if path in self.by_path:
            return self.by_path[path]
        fid = f"F{len(self.rows) + 1:02d}"
        row = {k: f[k] for k in ("value", "unit", "source", "window", "as_of") if k in f}
        for k in ("interval_95",):
            if k in f:
                row[k] = f[k]
        row["from"] = path
        self.rows[fid] = row
        self.by_path[path] = fid
        return fid

    def cite(self, path: str) -> tuple[str, str] | None:
        """(display, "[F01]") for the record figure at a dotted path, or None when the record has none there."""
        f = loop.get(self.record, path)
        if not loop.is_figure(f) or not isinstance(f.get("value"), int | float) or isinstance(f.get("value"), bool):
            return None
        return num(f), f"[{self.add(f, path)}]"

    def derived(self, value: Any, unit: str, source: str, window: tuple[str | None, str | None], as_of: str, path: str) -> tuple[str, str]:
        """A figure board-qa-prep reads out of a non-figure field of the record (such as a case count), given its own source."""
        f = loop.figure(value, unit, source, window[0], window[1], as_of)
        return num(f), f"[{self.add(f, path)}]"


# --- the brief -----------------------------------------------------------------------------------


def read_brief(record_path: Path, record: dict[str, Any]) -> dict[str, Any]:
    """The brief as the loop's shared parser reads it, its completeness, and whether it changed since the record opened."""
    p = loop.brief_path(record_path, record)
    out: dict[str, Any] = {"path": record["brief"]["path"], "file": p, "exists": p.exists(), "brief": None, "problems": [], "unchanged": None, "title": None}
    if not p.exists():
        out["problems"] = [f"the brief file {record['brief']['path']} is not there"]
        return out
    text = p.read_text(encoding="utf-8")
    title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), None)
    out["title"] = title
    out["unchanged"] = loop.sha256(p) == record["brief"].get("sha256")
    try:
        out["brief"] = landing_brief.parse(text)
    except landing_brief.BriefError as e:
        out["problems"] = [ln.strip() for ln in str(e).splitlines()[1:]] or [str(e)]
    return out


# --- questions -----------------------------------------------------------------------------------


class Draft:
    def __init__(self, record: dict[str, Any], ledger: Ledger, owner: str, due: str, as_of: str):
        self.record, self.ledger, self.owner, self.due, self.as_of = record, ledger, owner, due, as_of
        self.questions: list[dict[str, Any]] = []

    def answered(self, topic: str, question: str, answer: str, keys: list[str]) -> dict[str, Any]:
        q = {"id": "", "topic": topic, "question": question, "check": "answered", "answer": answer, "from_keys": keys}
        self.questions.append(q)
        return q

    def open(self, topic: str, question: str, missing: str, keys: list[str], owner: str | None = None) -> dict[str, Any]:
        q = {"id": "", "topic": topic, "question": question, "check": "open", "missing": missing, "owner": owner or self.owner, "due": self.due, "from_keys": keys}
        self.questions.append(q)
        return q


def has(record: dict[str, Any], key: str) -> bool:
    return isinstance(record.get(key), dict) and bool(record[key])


def run_line(key: str) -> str:
    return f"Not in the record yet: run {loop.WRITER[key]}."


def q_brief(d: Draft, b: dict[str, Any]) -> None:
    question = "What did we bet on, and how will we know it worked?"
    if b["brief"] is None:
        d.open("brief", question, "The landing brief cannot be used: " + "; ".join(b["problems"]) + ".", ["brief"])
        return
    br = b["brief"]
    bar = d.ledger.derived(br.bar, br.unit or "", f"landing brief {b['path']} (landing_brief.py)", (None, br.by), d.as_of, "brief/bar")
    better = "or higher" if br.higher_is_better else "or lower"
    d.answered("brief", question, f"{br.problem} The bar: {br.metric} at {bar[0]} {better} by {br.by} {bar[1]}. {br.decides} decides the next step.", ["brief"])
    if b["unchanged"] is False:
        d.open("brief", "The brief changed after the record opened. Which version is the board judging?", f"{b['path']} no longer matches the hash the record holds.", ["brief"])


def q_landed(d: Draft) -> None:
    r = d.record
    question = "Did it land?"
    if not has(r, "landed"):
        d.open("landed", question, run_line("landed") + " It sets the bet's status from the brief's bar and date.", ["landed"])
        return
    ld = r["landed"]
    cur, bar, at = (d.ledger.cite(f"landed/figures/{k}") for k in ("current", "bar", "at_date"))
    status = ld.get("status")
    if status not in ("landed", "watch", "stalled") or not cur or not bar:
        d.open("landed", question, "The landed key holds no status and figures that can be read.", ["landed"])
        return
    to = loop.get(r, "landed/figures/current/window/to")
    parts = [f"did-it-land says {status}. {ld.get('metric', 'The metric')} reads {cur[0]} {cur[1]} to {to}, against a bar of {bar[0]} {bar[1]} by {ld.get('by')}."]
    if at:
        parts.append(f"At the date it read {at[0]} {at[1]}.")
    codes = [str(fl.get("code")) for fl in ld.get("flags") or [] if isinstance(fl, dict) and fl.get("code")]
    if codes:
        parts.append("Flags on the read: " + ", ".join(codes) + ".")
    d.answered("landed", question, " ".join(parts), ["landed"])

    mean, sd, z = (d.ledger.cite(f"landed/figures/{k}") for k in ("baseline_mean", "baseline_sd", "move_z"))
    if mean and sd and z:
        d.answered(
            "noise",
            "Is the move real, or normal noise?",
            f"Before launch the metric averaged {mean[0]} {mean[1]}, with a spread of {sd[0]} {sd[1]}. "
            f"By the date it sat {z[0]} spreads above that mean {z[1]}. That rules out noise. It does not say what moved it: no holdout group is in the record.",
            ["landed"],
        )
    o_from, o_to = d.ledger.cite("landed/figures/outcome_from"), d.ledger.cite("landed/figures/outcome_to")
    if o_from and o_to:
        src = loop.get(r, "landed/figures/outcome_to/source")
        d.answered(
            "outcome",
            "Did the result the metric should move, move too?",
            f"The outcome series ({src}) went from {o_from[0]} {o_from[1]} on {loop.get(r, 'landed/figures/outcome_from/window/to')} "
            f"to {o_to[0]} {o_to[1]} on {loop.get(r, 'landed/figures/outcome_to/window/to')}. It moved the same way as the metric; the record does not show why.",
            ["landed"],
        )


def find_decisions(obj: Any) -> list[dict[str, Any]]:
    """Decision entries in a decisions key: dicts with a text field and an owner. Tolerant of the shape, since the key is new."""
    found: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        text = next((obj[k] for k in ("decision", "title", "question", "summary", "text") if isinstance(obj.get(k), str)), None)
        owner = next((obj[k] for k in ("owner", "decides", "decider", "decided_by") if isinstance(obj.get(k), str)), None)
        if text and owner:
            state = str(obj.get("status") or obj.get("state") or "").lower()
            found.append({"text": text, "owner": owner, "open": state not in ("decided", "made", "closed", "done", "agreed"), "due": obj.get("due") or obj.get("by")})
            return found
        for v in obj.values():
            found += find_decisions(v)
    elif isinstance(obj, list):
        for v in obj:
            found += find_decisions(v)
    return found


def q_decision(d: Draft) -> None:
    r = d.record
    question = "Do we scale it, and who decides?"
    if has(r, "decisions"):
        items = find_decisions(r["decisions"])
        still = [i for i in items if i["open"]]
        if still:
            first = still[0]
            names = "; ".join(i["text"] for i in still[:3])
            missing = f"{len(still)} decisions open in the decision record: {names}." if len(still) > 1 else f"Open in the decision record: {names}."
            d.open("decision", "Which decisions are still open, and who makes them?", check.strip_figures(missing), ["decisions"], owner=first["owner"])
        elif items:
            made = "; ".join(f"{i['text']} ({i['owner']})" for i in items[:3])
            d.answered("decision", "What did we decide, and who decided?", check.strip_figures(f"From the decision record: {made}."), ["decisions"])
        else:
            d.open("decision", question, "The decisions key holds no decision with an owner.", ["decisions"])
        return
    next_step = loop.get(r, "landed/next_step")
    owner = loop.get(r, "landed/decides") or d.owner
    lead = f"did-it-land's next step: {next_step} " if isinstance(next_step, str) else ""
    d.open("decision", question, check.strip_figures(lead) + "No decision is recorded yet: run decision-record.", ["landed", "decisions"], owner=owner)


def latest_eval_version(r: dict[str, Any]) -> str | None:
    rows = loop.get(r, "evals/rows")
    if isinstance(rows, list) and rows and isinstance(rows[-1], dict):
        return rows[-1].get("version")
    return loop.get(r, "evals/version")


def q_quality(d: Draft) -> None:
    r = d.record
    question = "Is quality holding as more of the work runs without a person?"
    if not has(r, "evals"):
        d.open("quality", question, run_line("evals"), ["evals"])
        return
    v = latest_eval_version(r)
    pr = d.ledger.cite(f"evals/figures/pass_rate@{v}")
    au = d.ledger.cite(f"evals/figures/autonomy_rate@{v}")
    if not pr:
        d.open("quality", question, f"The evals key holds no held-out pass rate for {v}.", ["evals"])
        return
    row = next((x for x in loop.get(r, "evals/rows") or [] if isinstance(x, dict) and x.get("version") == v), {})
    parts = [f"{v}'s held-out pass rate is {pr[0]} {pr[1]}"]
    iv = loop.get(r, f"evals/figures/pass_rate@{v}/interval_95")
    if isinstance(row.get("cases"), int):
        n = d.ledger.derived(
            row["cases"], "held-out cases", f"{r['evals'].get('skill', 'eval-kit')} {r['evals'].get('skill_version', '')}".strip() + f": evals.rows, {v}, cases",
            (row.get("run_at"), row.get("run_at")), r["evals"].get("as_of", ""), f"evals/rows/{v}/cases",
        )  # fmt: skip
        parts[0] += f" on {n[0]} cases {n[1]}"
    if isinstance(iv, list) and len(iv) == 2:
        parts[0] += f" (95% interval {sig(iv[0])}% to {sig(iv[1])}%)"
    parts[0] += "."
    if au:
        parts.append(f"{au[0]} of tasks finished with no person {au[1]}.")
    status = r["evals"].get("status")
    if status in ("meets target", "below target"):
        parts.append(f"eval-kit's build check: {status}.")
    d.answered("quality", question, " ".join(parts), ["evals"])

    prom = r["evals"].get("promotion")
    if isinstance(prom, dict) and prom.get("champion") and prom.get("challenger"):
        a, b = d.ledger.cite(f"evals/figures/pass_rate@{prom['champion']}"), pr
        if a and isinstance(prom.get("within_noise"), bool):
            noise = (
                "eval-kit marks the gain as inside the noise for this case count, so it is not yet a proven gain."
                if prom["within_noise"]
                else "eval-kit marks the gain as outside the noise."
            )
            d.answered(
                "eval-gain",
                f"Is {prom['challenger']} really better than {prom['champion']}?",
                f"Held-out pass rate went from {a[0]} {a[1]} on {prom['champion']} to {b[0]} {b[1]} on {prom['challenger']}, on the same cases. {noise}",
                ["evals"],
            )


def q_cost(d: Draft) -> None:
    r = d.record
    question = "What does each task cost, against the budget?"
    if not has(r, "cost"):
        d.open("cost", question, run_line("cost"), ["cost"])
        return
    act, bud = d.ledger.cite("cost/lines/cost_per_task/actual"), d.ledger.cite("cost/lines/cost_per_task/budget")
    if not act or not bud:
        d.open("cost", question, "The cost key holds no cost per task with its budget.", ["cost"])
        return
    status = loop.get(r, "cost/lines/cost_per_task/budget_status")
    over = d.ledger.cite("cost/lines/cost_per_task/against_budget")
    window = loop.get(r, "cost/lines/cost_per_task/actual/window") or {}
    parts = [f"{act[0]} per task {act[1]} from {window.get('from')} to {window.get('to')}, against a budget of {bud[0]} {bud[1]}"]
    if status in ("within budget", "over budget"):
        parts[0] += f": {status}"
        if status == "over budget" and over:
            parts[0] += f" by {over[0]} {over[1]}"
    parts[0] += "."
    tok = (d.ledger.cite("cost/lines/tokens_per_task/actual"), d.ledger.cite("cost/lines/tokens_per_task/budget"))
    ppt = (d.ledger.cite("cost/lines/price_per_token/actual"), d.ledger.cite("cost/lines/price_per_token/budget"))
    if all(tok):
        parts.append(f"Tokens per task: {tok[0][0]} {tok[0][1]} against {tok[1][0]} {tok[1][1]}.")
    if all(ppt):
        parts.append(f"Price per token: {ppt[0][0]} {ppt[0][1]} against {ppt[1][0]} {ppt[1][1]}.")
    parts.append("cost-budget-check computes these; eval-kit cites the same cost per task.")
    d.answered("cost", question, " ".join(parts), ["cost"])

    if loop.get(r, "cost/budget_status") == "over budget":
        model = loop.get(r, "cost/driver/model")
        drv, tot = d.ledger.cite("cost/driver/over_budget"), d.ledger.cite("cost/over_budget")
        detail = f"The record names the model behind most of it, {model}: {drv[0]} {drv[1]} of {tot[0]} {tot[1]} over budget. " if model and drv and tot else ""
        d.open("cost-owner", "Who brings cost back within budget, and by when?", detail + "It holds no plan and no owner for the fix.", ["cost"])


def q_spec_release(d: Draft) -> None:
    r = d.record
    if has(r, "release"):
        word = next((v for _, v in walk_strings(r["release"]) if v in ("ready to ship", "hold")), None)
        if word:
            as_of = r["release"].get("as_of", "")
            d.answered("release", "Was it ready to ship when it shipped?", f"release-readiness says {word}{' as of ' + as_of if as_of else ''}.", ["release"])
            if word == "hold":
                d.open("release", "What is holding the release, and who clears it?", "release-readiness says hold.", ["release"])
            return
        d.open("release", "Was it ready to ship when it shipped?", "The release key holds no ready to ship or hold word.", ["release"])
        return
    if has(r, "spec"):
        verdict = r["spec"].get("verdict")
        holds = [h for h in r["spec"].get("holds") or [] if isinstance(h, dict)]
        n = d.ledger.cite("spec/counts/hold")
        if verdict == "hold" and holds:
            what = " ".join(check.strip_figures(str(h.get("message") or h.get("check"))) for h in holds[:3])
            count = f"{n[0]} findings {n[1]}" if n else "findings"
            d.open(
                "spec",
                "Were the spec's holds fixed before it shipped?",
                f"spec-auditor held the spec on {count} on {r['spec'].get('as_of')}: {what} No later audit or release check is in the record: run release-readiness.",
                ["spec", "release"],
            )
            return
        if verdict == "pass":
            d.answered("spec", "Did the spec pass review before build?", f"spec-auditor says pass, as of {r['spec'].get('as_of')}.", ["spec"])
            return
    d.open("release", "Was it ready to ship when it shipped?", run_line("release"), ["release"])


def walk_strings(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(obj, str):
        return [(prefix, obj)]
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += walk_strings(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += walk_strings(v, f"{prefix}[{i}]")
    return out


def humanise(name: str) -> str:
    last = name.split("/")[-1]
    return last.replace("_", " ").replace("@", " for ")


def q_portfolio(d: Draft) -> None:
    r = d.record
    if not has(r, "portfolio"):
        return
    rank, score = d.ledger.cite("portfolio/rank"), d.ledger.cite("portfolio/brief_score")
    if not rank:
        return
    unit = str(loop.get(r, "portfolio/rank/unit") or "")
    text = f"bet-portfolio-review ranked it {rank[0]} {unit.removeprefix('rank ')} {rank[1]} on {r['portfolio'].get('as_of')}"
    if score:
        text += f". Its brief scored {score[0]} {loop.get(r, 'portfolio/brief_score/unit')} {score[1]}"
    d.answered("portfolio", "Why this bet, over the others?", text + ".", ["portfolio"])


def q_signals(d: Draft) -> None:
    r = d.record
    question = "What are customers saying about it?"
    if not has(r, "signals"):
        d.open("signals", question, run_line("signals"), ["signals"])
        return
    figs = loop.figures_in(r["signals"])
    numeric = [(n, f) for n, f in figs if isinstance(f.get("value"), int | float) and not isinstance(f.get("value"), bool)][:3]
    if not numeric:
        d.open("signals", question, "The signals key holds no figure with a source.", ["signals"])
        return
    bits = []
    for name, _ in numeric:
        c = d.ledger.cite(f"signals/{name}")
        if c:
            bits.append(f"{humanise(name)} {c[0]} {c[1]}")
    d.answered("signals", question, "From customer-signal-digest: " + "; ".join(bits) + ".", ["signals"])


def find_fixes(obj: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        text = next((obj[k] for k in ("fix", "action", "title", "what") if isinstance(obj.get(k), str)), None)
        owner = obj.get("owner") if isinstance(obj.get("owner"), str) else None
        if text and owner:
            state = str(obj.get("status") or obj.get("state") or "").lower()
            return [{"text": text, "owner": owner, "done": state in ("done", "fixed", "closed", "shipped")}]
        for v in obj.values():
            found += find_fixes(v)
    elif isinstance(obj, list):
        for v in obj:
            found += find_fixes(v)
    return found


def q_postmortem(d: Draft) -> None:
    r = d.record
    question = "What went wrong, and who owns each fix?"
    if not has(r, "postmortem"):
        if loop.get(r, "landed/status") == "stalled":
            d.open("postmortem", question, run_line("postmortem"), ["postmortem"])
        return
    fixes = find_fixes(r["postmortem"])
    left = [f for f in fixes if not f["done"]]
    if left:
        names = "; ".join(f"{f['text']} ({f['owner']})" for f in left[:3])
        d.open("postmortem", question, check.strip_figures(f"Fixes not yet done: {names}."), ["postmortem"], owner=left[0]["owner"])
    elif fixes:
        names = "; ".join(f"{f['text']} ({f['owner']})" for f in fixes[:3])
        d.answered("postmortem", question, check.strip_figures(f"From the postmortem, every fix is done: {names}."), ["postmortem"])
    else:
        d.open("postmortem", question, "The postmortem key holds no fix with an owner.", ["postmortem"])


# --- questions asked last time -------------------------------------------------------------------


def read_past(path: Path) -> list[str]:
    """One question per line (a Markdown list works), or a CSV with a question column."""
    if path.stat().st_size > MAX_PAST_BYTES:
        raise PrepError(f"{path} is over {MAX_PAST_BYTES:,} bytes, so it is not a list of questions.")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(io.StringIO(text)))
        col = next((c for c in (rows[0].keys() if rows else []) if c and c.strip().lower() == "question"), None)
        if col is None:
            raise PrepError(f"{path} has no question column.")
        return [r[col].strip() for r in rows if (r.get(col) or "").strip()]
    out = []
    for line in text.splitlines():
        s = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", line).strip()
        if s.endswith("?") and not s.startswith("#"):
            out.append(s)
    return out


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP}


def place_past(d: Draft, past: list[str]) -> None:
    for text in past:
        w = words(text)
        best, score = None, 0
        for topic, vocab in TOPIC_WORDS.items():
            s = len(w & vocab)
            if s > score and any(q["topic"] == topic for q in d.questions):
                best, score = topic, s
        if best:
            q = next(q for q in d.questions if q["topic"] == best)
            q.setdefault("asked_last_time", []).append(text)
        else:
            q = d.open("past", text, "Nothing in the record answers it, so it needs a person's answer.", [])
            q["asked_last_time"] = [text]


# --- the key -------------------------------------------------------------------------------------


def prep(
    record_path: Path, past: Path | None = None, owner: str | None = None, due: str = DEFAULT_DUE, as_of: str | None = None, illustrative: bool | None = None
) -> dict[str, Any]:
    """The board_qa key for a record. Pure: reads files, writes nothing."""
    record = loop.load(record_path)
    as_of = as_of or datetime.date.today().isoformat()
    try:
        datetime.date.fromisoformat(as_of)
    except ValueError:
        raise PrepError(f"--as-of {as_of!r} is not a date. Write YYYY-MM-DD.") from None
    b = read_brief(record_path, record)
    owner = owner or (b["brief"].decides if b["brief"] else None) or loop.get(record, "landed/decides")
    if not owner or check.placeholder(owner):
        raise PrepError("no owner for open questions: the brief names no one who decides. Pass --owner with a person or a role.")
    ledger = Ledger(record)
    d = Draft(record, ledger, owner, due, as_of)
    q_brief(d, b)
    q_landed(d)
    q_decision(d)
    q_quality(d)
    q_cost(d)
    q_spec_release(d)
    q_signals(d)
    q_postmortem(d)
    q_portfolio(d)
    if past:
        place_past(d, read_past(past))
    for i, q in enumerate(d.questions, start=1):
        q["id"] = f"Q{i:02d}"
        q["priority"] = WEIGHT.get(q["topic"], 1) + (2 if q["check"] == "open" else 0) + (3 if q.get("asked_last_time") else 0)
    first = [q["id"] for q in sorted(d.questions, key=lambda q: (-q["priority"], q["id"]))[:5]]
    counts_src = f"{TOOL}: count of questions in board_qa"
    n_open = sum(q["check"] == "open" for q in d.questions)
    present = [k for k in loop.READS if has(record, k)]
    if illustrative is None:
        illustrative = bool(loop.get(record, "evals/illustrative")) or "illustrative" in (b["file"].read_text(encoding="utf-8").lower() if b["exists"] else "")
    return {
        "tool": TOOL,
        "as_of": as_of,
        "bet_title": b["title"] or record["bet"],
        "read": present,
        "not_in_record": [k for k in loop.READS if k not in present],
        "brief": {"path": b["path"], "complete": b["brief"] is not None, "problems": b["problems"], "unchanged": b["unchanged"]},
        "counts": {
            "questions": loop.figure(len(d.questions), "questions", counts_src, as_of, as_of, as_of),
            "answered": loop.figure(len(d.questions) - n_open, "questions", counts_src, as_of, as_of, as_of),
            "open": loop.figure(n_open, "questions", counts_src, as_of, as_of, as_of),
        },
        "first": first,
        "questions": d.questions,
        "figures": ledger.rows,
        "illustrative": illustrative,
    }


def write_pages(record: dict[str, Any], html_out: Path | None, md_out: Path | None) -> None:
    if html_out:
        html_out.parent.mkdir(parents=True, exist_ok=True)
        html_out.write_text(render_html.page(record), encoding="utf-8")
    if md_out:
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(render_html.markdown(record), encoding="utf-8")


def guarded_save(path: Path, record: dict[str, Any], key: dict[str, Any]) -> list[dict[str, Any]]:
    """Save the key only when the check passes. Returns the errors (empty when saved)."""
    errors = check.check({**record, loop.KEY: key})
    if not errors:
        loop.write(path, record, key)
    return errors


def report(errors: list[dict[str, Any]]) -> None:
    for e in errors:
        print(f"{e['question'] or '-'} {e['code']}: {e['message']}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep", help="draft the board questions and write the board_qa key")
    p.add_argument("record", type=Path)
    p.add_argument("--past", type=Path, help="questions the board asked last time: one per line, or a CSV with a question column")
    p.add_argument("--owner", help="who owns open questions (default: the brief's 'Decides the next step')")
    p.add_argument("--due", default=DEFAULT_DUE, help=f"when open questions are due (default: {DEFAULT_DUE})")
    p.add_argument("--as-of", help="the date of the prep, YYYY-MM-DD (default: today)")
    p.add_argument("--html", type=Path)
    p.add_argument("--md", type=Path)
    c = sub.add_parser("check", help="check the board_qa key")
    c.add_argument("record", type=Path)
    e = sub.add_parser("edit", help="reword one question; saved only when the check passes")
    e.add_argument("record", type=Path)
    e.add_argument("id")
    e.add_argument("--question")
    e.add_argument("--answer")
    e.add_argument("--missing")
    k = sub.add_parser("close", help="record a stated answer from a named person; saved only when the check passes")
    k.add_argument("record", type=Path)
    k.add_argument("id")
    k.add_argument("--text", required=True)
    k.add_argument("--by", required=True)
    r = sub.add_parser("render", help="render the board_qa key as HTML and Markdown")
    r.add_argument("record", type=Path)
    r.add_argument("--html", type=Path)
    r.add_argument("--md", type=Path)
    a = ap.parse_args(argv)
    try:
        record = loop.load(a.record)
        if a.cmd == "prep":
            key = prep(a.record, a.past, a.owner, a.due, a.as_of)
            errors = guarded_save(a.record, record, key)
            if errors:
                report(errors)
                return 1
            saved = loop.load(a.record)
            write_pages(saved, a.html, a.md)
            n = key["counts"]
            print(f"board_qa: {n['questions']['value']} questions, {n['answered']['value']} answered, {n['open']['value']} open. Prepare first: {', '.join(key['first'])}.")
            print(f"Wrote the board_qa key of {a.record}" + "".join(f", {x}" for x in (a.html, a.md) if x) + ".")
            return 0
        if loop.KEY not in record:
            print(f"{a.record} has no board_qa key. Run prep first.", file=sys.stderr)
            return 2
        if a.cmd == "check":
            errors = check.check(record)
            report(errors)
            print(f"check: {len(errors)} errors.")
            return 1 if errors else 0
        if a.cmd == "render":
            errors = check.check(record)
            if errors:
                report(errors)
                return 1
            write_pages(record, a.html, a.md)
            return 0
        key = dict(record[loop.KEY])
        key["questions"] = [dict(q) for q in key["questions"]]
        q = next((q for q in key["questions"] if q["id"] == a.id), None)
        if q is None:
            print(f"there is no question {a.id}.", file=sys.stderr)
            return 2
        if a.cmd == "edit":
            for field in ("question", "answer", "missing"):
                value = getattr(a, field)
                if value is not None:
                    if field != "question" and field not in q:
                        print(f"{a.id} is {q['check']}; it has no {field} to edit.", file=sys.stderr)
                        return 2
                    q[field] = value
        else:
            q.update({"check": "answered", "answer": a.text, "stated_by": a.by})
            for gone in ("missing", "owner", "due"):
                q.pop(gone, None)
        n_open = sum(x["check"] == "open" for x in key["questions"])
        key["counts"] = {**key["counts"], "answered": {**key["counts"]["answered"], "value": len(key["questions"]) - n_open}, "open": {**key["counts"]["open"], "value": n_open}}
        errors = guarded_save(a.record, record, key)
        if errors:
            report(errors)
            print("Not saved.", file=sys.stderr)
            return 1
        print(f"Saved {a.id}.")
        return 0
    except (loop.RecordError, PrepError, OSError) as err:
        print(f"board-qa-prep: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
