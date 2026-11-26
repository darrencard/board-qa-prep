"""Check a board Q&A prep file. Deterministic; the model never grades itself.

Errors (any one blocks render.py):
  figure-not-in-ledger   a figure in an answer matches no figure in the rows it cites
  cite-missing           an answered question cites no ledger row and is not a stated answer
  stated-has-figure      a stated answer (stated_by a named person) contains a figure
  stated-no-name         stated_by is a placeholder, not a named person or role
  cite-unknown-row       an answer cites an ID the ledger does not have
  cite-unknown-confidence an answer rests on a row whose confidence is Unknown
  confidence-label-missing an answer cites an Estimated row without saying "estimated"
  gap-no-owner           a gap has no named owner
  gap-has-answer         a gap carries answer text with figures or citations
  status-word            an answer uses a status word other than landed, watch or stalled
  causal-claim           an answer says one thing caused another; the ledger shows what moved, not why
  bad-status             status is not "answered" or "gap"
  empty-question         a question has no text
  duplicate-id           two questions share an ID

Usage: python3 scripts/check.py qa.json [--json]
Exit code 0 when there are no errors, 1 otherwise, 2 when the file cannot be read.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from figures import figures, unmatched  # noqa: E402
from questions import row_figures  # noqa: E402

CITE_RE = re.compile(r"\[\[?(L\d{1,3})\]?\]")
PLACEHOLDER_OWNERS = {"", "tbd", "tbc", "unassigned", "unknown", "none", "n/a", "na", "?", "someone", "owner"}
STATUS_RE = re.compile(r"\b(on track|off track|at risk|green|amber|red status|rag)\b", re.IGNORECASE)
CAUSAL_RE = re.compile(
    r"\b(caused|causes|drove|driven by|because of|due to|thanks to|as a result of|led to|resulted in|proves?|proved)\b",
    re.IGNORECASE,
)


def check(qa: dict) -> list[dict]:
    ledger = {str(r.get("id")): r for r in qa.get("ledger") or []}
    problems: list[dict] = []
    seen_ids: set[str] = set()

    def err(q: dict, code: str, message: str) -> None:
        problems.append({"question": q.get("id"), "slide": q.get("slide"), "code": code, "message": message})

    for q in qa.get("questions") or []:
        qid = str(q.get("id"))
        if qid in seen_ids:
            err(q, "duplicate-id", f"{qid} is used twice.")
        seen_ids.add(qid)
        if not str(q.get("question") or "").strip():
            err(q, "empty-question", "The question has no text.")
        status = q.get("status")
        answer = str(q.get("answer") or "")

        if status == "gap":
            gap = q.get("gap") or {}
            owner = str(gap.get("owner") or "").strip()
            if owner.lower() in PLACEHOLDER_OWNERS:
                err(q, "gap-no-owner", "A gap needs a named owner (a person or a role), not a placeholder.")
            if answer.strip() and (figures(answer) or CITE_RE.search(answer)):
                err(q, "gap-has-answer", "A gap cannot carry figures or citations. Answer it from the ledger or leave the answer empty.")
            continue
        if status != "answered":
            err(q, "bad-status", f"status is {status!r}; use 'answered' or 'gap'.")
            continue

        cites = CITE_RE.findall(answer)
        stated_by = q.get("stated_by")
        if stated_by is not None:
            if str(stated_by).strip().lower() in PLACEHOLDER_OWNERS:
                err(q, "stated-no-name", "stated_by must name the person or role who gave the answer.")
            if not cites and figures(answer):
                err(q, "stated-has-figure", "A stated answer cannot carry a figure. Cite the ledger row that holds it, or remove it.")
        if not cites and (stated_by is None or not answer.strip()):
            err(q, "cite-missing", "An answer must cite a ledger row, as [L08], or be a figure-free answer stated_by a named person. Otherwise make it a gap.")
            continue
        rows = []
        for cid in dict.fromkeys(cites):
            row = ledger.get(cid)
            if row is None:
                err(q, "cite-unknown-row", f"{cid} is not in the evidence ledger.")
                continue
            confidence = str(row.get("confidence") or "Unknown").lower()
            if confidence == "unknown":
                err(q, "cite-unknown-confidence", f"{cid} is Unknown; it cannot answer a board question. Make this a gap.")
            if confidence == "estimated" and not re.search(r"\bestimat", answer, re.IGNORECASE):
                err(q, "confidence-label-missing", f"{cid} is Estimated; the answer must say so.")
            rows.append(row)

        allowed = [f for row in rows for f in row_figures(row)]
        for fig in unmatched(answer, allowed) if cites else []:  # a stated answer is checked above
            elsewhere = [rid for rid, row in ledger.items() if any(fig.matches(f) for f in row_figures(row))]
            hint = f" It matches {', '.join(elsewhere)}; cite that row." if elsewhere else " No ledger row holds it."
            err(q, "figure-not-in-ledger", f"{fig.text} is not in the rows cited ({', '.join(dict.fromkeys(cites))}).{hint}")

        if STATUS_RE.search(answer):
            err(q, "status-word", f"'{STATUS_RE.search(answer).group(0)}' is not a status word here. Use landed, watch or stalled.")
        if CAUSAL_RE.search(answer):
            err(q, "causal-claim", f"'{CAUSAL_RE.search(answer).group(0)}' claims a cause. The ledger shows what moved, not why.")
    return problems


def summary(qa: dict, problems: list[dict]) -> str:
    qs = qa.get("questions") or []
    gaps = sum(q.get("status") == "gap" for q in qs)
    lines = [f"{len(qs)} questions, {len(qs) - gaps} answered, {gaps} gaps, {len(problems)} errors."]
    for p in problems:
        lines.append(f"  {p['question']} (slide {p['slide']}) {p['code']}: {p['message']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check every answer cites the ledger and every gap has an owner.")
    p.add_argument("qa")
    p.add_argument("--json", action="store_true", help="Print the problems as JSON.")
    args = p.parse_args(argv)
    try:
        qa = json.loads(Path(args.qa).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {args.qa}: {exc}", file=sys.stderr)
        return 2
    problems = check(qa)
    print(json.dumps(problems, indent=2) if args.json else summary(qa, problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
