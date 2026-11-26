"""Render the prep pack as Markdown. Refuses while check.py reports any error.

The pack has three parts: the questions by slide with their answers, the gaps
with owners and due dates, and the ledger rows the answers cite. Every piece of
text from the deck is escaped, so a slide cannot add HTML or break a table.

Usage: python3 scripts/render.py qa.json --out prep.md
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check import CITE_RE, check, summary  # noqa: E402


def esc(text) -> str:
    """Escape text from a deck for Markdown: no HTML, no table breaks, no new lines."""
    text = html.escape(" ".join(str(text if text is not None else "").split()), quote=False)
    return text.replace("|", "\\|")


def render(qa: dict) -> str:
    meta = qa.get("deck") or {}
    qs = qa.get("questions") or []
    ledger = {str(r.get("id")): r for r in qa.get("ledger") or []}
    gaps = [q for q in qs if q.get("status") == "gap"]
    head = " ".join(esc(x) for x in (meta.get("company"), meta.get("period")) if x) or "Board deck"
    cut = {"B": "the board cut", "L": "the leadership cut", "S": "the staff cut"}.get(meta.get("cut"), "the deck")

    out = [f"# Board Q&A prep: {head}", ""]
    if meta.get("illustrative"):
        out += ["> Illustrative. The deck is marked as a sample, so every figure here is illustrative.", ""]
    out += [
        f"{len(qs)} likely questions from {cut}. {len(qs) - len(gaps)} have an answer from the evidence ledger; {len(gaps)} are gaps, each with an owner.",
        "",
        "Every figure in an answer comes from the ledger row it cites. A question without a sourced answer is a gap, not a guess.",
        "",
        "## Questions by slide",
        "",
    ]
    current = None
    for q in qs:
        if q.get("slide") != current:
            current = q.get("slide")
            out += [f"### Slide {esc(current)}: {esc(q.get('slide_title'))}", ""]
        out.append(f"**{esc(q.get('id'))}. {esc(q.get('question'))}**")
        out.append("")
        if q.get("status") == "gap":
            gap = q.get("gap") or {}
            due = f", due {esc(gap.get('due'))}" if gap.get("due") else ""
            out.append(f"Gap. {esc(gap.get('what'))} Owner: {esc(gap.get('owner'))}{due}.")
        else:
            out.append(esc(q.get("answer")))
        out.append("")

    out += ["## Gaps to close before the meeting", ""]
    if gaps:
        out += ["| Question | Slide | What is missing | Owner | Due |", "|---|---|---|---|---|"]
        for q in gaps:
            gap = q.get("gap") or {}
            out.append(
                f"| {esc(q.get('id'))} {esc(q.get('question'))} | {esc(q.get('slide'))} | {esc(gap.get('what'))} | "
                f"{esc(gap.get('owner'))} | {esc(gap.get('due') or 'not set')} |"
            )
    else:
        out.append("None. Every question has a sourced answer.")
    out.append("")

    cited = sorted({c for q in qs if q.get("status") == "answered" for c in CITE_RE.findall(str(q.get("answer") or ""))})
    out += ["## Ledger rows cited", ""]
    if cited:
        out += ["| ID | Claim | Source | Window | Confidence |", "|---|---|---|---|---|"]
        for cid in cited:
            r = ledger.get(cid, {})
            out.append(f"| {esc(cid)} | {esc(r.get('claim'))} | {esc(r.get('source'))} | {esc(r.get('window'))} | {esc(r.get('confidence'))} |")
    else:
        out.append("None.")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render the board Q&A prep pack as Markdown, after the check passes.")
    p.add_argument("qa")
    p.add_argument("--out", default="prep.md")
    args = p.parse_args(argv)
    try:
        qa = json.loads(Path(args.qa).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {args.qa}: {exc}", file=sys.stderr)
        return 2
    problems = check(qa)
    if problems:
        print("Not rendered. Fix these first:\n" + summary(qa, problems), file=sys.stderr)
        return 1
    Path(args.out).write_text(render(qa), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
