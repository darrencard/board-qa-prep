"""Check the board_qa key of a Landing Loop record. Deterministic; the model never grades itself.

Errors (any one blocks a save and a render):
  figure-not-cited     a figure in a question, answer or missing line matches no figure the text cites as [F01]
  cite-unknown         the text cites a figure ID the key does not hold
  figure-shape         a figure lacks value, unit, source, window (from, to) or as_of, or has an empty source
  figure-changed       a figure copied from the record no longer matches the record at its `from` path
  check-word           check is not "answered" or "open"
  open-no-owner        an open question has no owner, or a placeholder such as TBD
  open-no-missing      an open question does not say what is missing
  answered-no-source   an answered question cites no figure, names no record key, and is not a stated answer
  stated-no-name       a stated answer's stated_by is a placeholder
  status-word          landed, watch or stalled outside the "Did it land?" answer, or one that is not landed.status;
                       or a status word the loop does not use (on track, at risk, green, amber, RAG)
  causal-claim         an answer says one thing caused another; the record shows what moved, not why
  empty-question       a question has no text
  duplicate-id         two questions share an ID

Usage: python3 check.py landing/<bet>.json
Standard library only. Python 3.11 or later.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import loop  # noqa: E402
from display import num, sig  # noqa: E402
from figures import Figure, figures  # noqa: E402

CITE = re.compile(r"\[(F\d{1,3})\]")
PLACEHOLDERS = {"", "tbd", "tbc", "unassigned", "unknown", "none", "n/a", "na", "?", "someone", "owner", "todo"}
BET_STATUS = re.compile(r"\b(landed|watch|stalled)\b", re.I)
OTHER_STATUS = re.compile(r"\b(on track|off track|at risk|green|amber|red status|rag)\b", re.I)
CAUSAL = re.compile(r"\b(caused|causes|drove|driven by|because of|due to|thanks to|as a result of|led to|resulted in|proves?|proved)\b", re.I)
REQUIRED = ("value", "unit", "source", "window", "as_of")


def placeholder(name: Any) -> bool:
    return not isinstance(name, str) or name.strip().lower() in PLACEHOLDERS


def strip_figures(text: str) -> str:
    """Text quoted from another key, with any figure it holds replaced, since board_qa may print only figures it cites."""
    found = figures(text)
    for f in sorted(found, key=lambda f: -len(f.text)):
        text = text.replace(f.text, "(see the record)")
    return text


def allowed(f: dict[str, Any]) -> list[Figure]:
    """The figures a citation of f lets the text print: its value as displayed, the numbers in its unit, and its interval."""
    out = figures(num(f)) + figures(str(f.get("unit") or ""))
    if str(f.get("unit") or "").lower().startswith("point") and isinstance(f.get("value"), int | float):
        out.append(Figure("pct", float(f["value"]), "points"))  # "14 points" reads as points, as the unit says
    iv = f.get("interval_95")
    if isinstance(iv, list):
        out += [Figure("pct", 95.0, "95%")] + [x for v in iv for x in figures(f"{sig(v)}%")]
    return out


def check(record: dict[str, Any]) -> list[dict[str, Any]]:
    key = record.get(loop.KEY) or {}
    problems: list[dict[str, Any]] = []

    def err(qid: Any, code: str, message: str) -> None:
        problems.append({"question": qid, "code": code, "message": message})

    figs = key.get("figures") or {}
    for fid, f in figs.items():
        if not isinstance(f, dict) or any(k not in f for k in REQUIRED) or not f.get("source") or not isinstance(f.get("window"), dict) or set(f["window"]) != {"from", "to"}:
            err(None, "figure-shape", f"{fid} needs value, unit, source, window (from, to) and as_of.")
            continue
        src = f.get("from", "")
        if src and not src.startswith(("brief/", "evals/rows/")):
            there = loop.get(record, src)
            if not loop.is_figure(there) or there.get("value") != f["value"] or there.get("source") != f["source"]:
                err(None, "figure-changed", f"{fid} no longer matches {src} in the record.")
    for name, f in (key.get("counts") or {}).items():
        if not isinstance(f, dict) or any(k not in f for k in REQUIRED):
            err(None, "figure-shape", f"counts.{name} needs value, unit, source, window and as_of.")

    status = (record.get("landed") or {}).get("status")
    seen: set[str] = set()
    for q in key.get("questions") or []:
        qid = q.get("id")
        if qid in seen:
            err(qid, "duplicate-id", f"{qid} is used twice.")
        seen.add(qid)
        if not str(q.get("question") or "").strip():
            err(qid, "empty-question", "The question has no text.")
        word = q.get("check")
        if word not in ("answered", "open"):
            err(qid, "check-word", f"check is {word!r}; use answered or open.")
            continue
        if word == "open":
            if placeholder(q.get("owner")):
                err(qid, "open-no-owner", "An open question needs a named owner: a person or a role.")
            if not str(q.get("missing") or "").strip():
                err(qid, "open-no-missing", "Say what is missing.")
        else:
            body = str(q.get("answer") or "")
            if "stated_by" in q:
                if placeholder(q.get("stated_by")):
                    err(qid, "stated-no-name", "Name the person or role who gave the answer.")
            elif not CITE.search(body) and not q.get("from_keys"):
                err(qid, "answered-no-source", "Cite a figure as [F01], or record who said it with close --by.")
        for field in ("question", "answer", "missing"):
            text = str(q.get(field) or "")
            if not text:
                continue
            cited = CITE.findall(text)
            ok: list[Figure] = []
            for fid in cited:
                if fid not in figs:
                    err(qid, "cite-unknown", f"{field} cites {fid}, which the key does not hold.")
                else:
                    ok += allowed(figs[fid])
            for f in figures(text):
                if not any(f.matches(a) for a in ok):
                    err(qid, "figure-not-cited", f"{field}: {f.text!r} matches no figure it cites. Cite the record figure, or remove it.")
            for m in BET_STATUS.finditer(text):
                if q.get("topic") != "landed" or field != "answer" or m.group(1).lower() != status:
                    err(qid, "status-word", f"{field}: {m.group(1)!r} is a bet status. Only the 'Did it land?' answer prints it, as did-it-land set it.")
            m = OTHER_STATUS.search(text)
            if m:
                err(qid, "status-word", f"{field}: {m.group(1)!r} is not a loop word. A bet is landed, watch or stalled; a question is answered or open.")
            if field != "question":
                m = CAUSAL.search(text)
                if m:
                    err(qid, "causal-claim", f"{field}: {m.group(1)!r}. Say what moved and when, not why.")
    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    errors = check(record)
    for e in errors:
        print(f"{e['question'] or '-'} {e['code']}: {e['message']}")
    print(f"check: {len(errors)} errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
