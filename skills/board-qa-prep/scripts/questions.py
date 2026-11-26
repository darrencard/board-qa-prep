"""Draft the likely board questions for each slide, and an answer for each.

Questions come from fixed rules, matched on the slide's own words, so the same
deck always yields the same questions. Claude adds or rewrites questions after
this, and check.py holds every answer to the same rules.

An answer is drafted only from ledger rows, quoting each row's claim and
citing it as [L08]. A question no ledger row answers becomes a gap with an
owner and a due date. So does a figure printed on a slide that no ledger row
holds, and every "Data needed" block the deck already declares.

Output: qa.json
  {"deck": {...}, "questions": [{"id", "slide", "slide_title", "rule", "question",
    "status": "answered" | "gap", "answer", "gap": {"what", "owner", "due"} | null}]}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deck as deck_mod  # noqa: E402
from figures import Figure, figures, value_figures  # noqa: E402

MAX_PER_SLIDE = 6
MAX_UNSOURCED = 3
MAX_ROWS = 2


def _rx(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


# (rule, slide trigger, question, ledger topic). Order is priority order.
RULES = [
    (
        "decision",
        _rx(r"\b(decisions?|decide|approve|approval|need from|we need)\b"),
        "What exactly is the board asked to decide, by when, and what happens if it does not?",
        _rx(r"\bdecision"),
    ),
    (
        "plan",
        _rx(r"\b(plan|target|behind|short|missed|did not|over plan|under plan)\b"),
        "What closes the gap to plan, who owns it and by when?",
        _rx(r"\b(target|against plan|vs plan|over plan|forecast)\b"),
    ),
    (
        "quality",
        _rx(r"\b(faster|throughput|cycle time|velocity|lead time|deploys?|deployment frequency)\b"),
        "Speed is up. What did quality do over the same window?",
        _rx(r"\b(review|change fail|incident|defect|quality|eval|bug|rollback|escaped)\b"),
    ),
    (
        "unit-cost",
        _rx(r"(\$|\bcost|\bspend|\binference|\bbudget|\bburn)"),
        "What does each unit of work cost now, and what is the ceiling?",
        _rx(r"\b(cost per|per task|per engineer|per seat|per load)\b"),
    ),
    (
        "ai-margin",
        _rx(r"\b(AI|agent|agents|model|LLM|assistant|eval)\b"),
        "Does the AI feature pay for itself: what does it earn against what it costs to run?",
        _rx(r"\b(margin|cost per|gross margin)\b"),
    ),
    (
        "revenue",
        _rx(r"\b(ARR|revenue|expansion|retention|churn|NRR|GRR|bookings)\b"),
        "Does this figure match Finance's close for the same date?",
        _rx(r"\b(ARR|revenue|expansion|retention|churn|NRR|GRR|bookings)\b"),
    ),
    (
        "risk",
        _rx(r"\b(risks?|depend\w*|provider|single point|exposure|concentration)\b"),
        "What is the mitigation, who owns it, and when does the exposure fall?",
        _rx(r"\b(risk|provider|segment|depend\w*|exposure)\b"),
    ),
    (
        "stop-rule",
        _rx(r"\b(bets?|experiment|probe|pilot)\b"),
        "What is the stop rule for each bet, and who calls it?",
        _rx(r"\b(stop rule|bet)\b"),
    ),
    (
        "people",
        _rx(r"\b(hire|hiring|headcount|roles|attrition|team size)\b"),
        "Which open role is the constraint, and when will it be filled?",
        _rx(r"\b(headcount|roles|hire|attrition)\b"),
    ),
    (
        "impact",
        _rx(r"\b(commitments?|roadmap|shipped|launched)\b"),
        "Of what shipped, which moved the outcome it was meant to move?",
        _rx(r"\b(moved|landed|outcome)\b"),
    ),
]

UNCITABLE = {"unknown"}


def row_figures(row: dict) -> list[Figure]:
    out: list[Figure] = []
    for key in ("claim", "window", "source"):
        out.extend(figures(row.get(key)))
    out.extend(value_figures(row.get("value"), row.get("unit")))
    return out


def _clip(text: str, n: int = 90) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "..."


def draft_answer(rows: list[dict]) -> str:
    parts = []
    for row in rows:
        bits = [str(row.get("confidence") or "Unknown")]
        if row.get("window"):
            bits.append(str(row["window"]))
        if row.get("source"):
            bits.append(f"source: {row['source']}")
        claim = str(row.get("claim") or "").strip().rstrip(".")
        prefix = "Estimated: " if str(row.get("confidence")).lower() == "estimated" else ""
        parts.append(f"{prefix}{claim} ({'; '.join(bits)}) [{row['id']}].")
    return " ".join(parts)


def _pick_rows(slide: dict, ledger: dict, topic: re.Pattern | None) -> tuple[list[dict], list[dict]]:
    """Rows that answer the question, and cited-but-Unknown rows that cannot."""
    on_slide = [ledger[r] for r in slide["ledger_refs"] if r in ledger]
    if topic is None:
        pool = on_slide
    else:
        pool = [r for r in on_slide if topic.search(r["claim"])]
        if not pool:
            pool = [r for r in ledger.values() if topic.search(r["claim"])]
    usable = [r for r in pool if str(r.get("confidence")).lower() not in UNCITABLE]
    unknown = [r for r in pool if str(r.get("confidence")).lower() in UNCITABLE]
    return usable[:MAX_ROWS], unknown


def _headline_rows(slide: dict, ledger: dict) -> tuple[list[dict], list[dict]]:
    """Rows that hold the title's figures; with no figures in the title, the slide's own rows."""
    title_figs = figures(slide["title"])
    if not title_figs:
        return _pick_rows(slide, ledger, None)
    pool = [r for r in ledger.values() if any(t.matches(f) for t in title_figs for f in row_figures(r))]
    pool.sort(key=lambda r: r["id"] not in slide["ledger_refs"])
    usable = [r for r in pool if str(r.get("confidence")).lower() not in UNCITABLE]
    unknown = [r for r in pool if str(r.get("confidence")).lower() in UNCITABLE]
    return usable[:MAX_ROWS], unknown


def _home(rule: tuple, slides: list[dict]) -> str | None:
    """The one slide a topic question belongs to: the slide that raises it most.

    A hit in the title counts 3, a hit in the body 1. Ties go to the earlier slide.
    """
    trigger = rule[1]
    best, best_score = None, 0
    for slide in slides:
        score = 3 * len(trigger.findall(slide["title"])) + len(trigger.findall(slide["text"]))
        if score > best_score:
            best, best_score = slide["id"], score
    return best


def _worth_asking(fig: Figure, in_title: bool) -> bool:
    """A figure in a title is always worth a question. In the body, skip bare small counts."""
    return in_title or fig.kind != "num" or fig.value >= 10


def generate(deck: dict, gap_owner: str, gap_due: str | None = None) -> dict:
    ledger = {r["id"]: r for r in deck["ledger"]}
    all_ledger_figs = [f for r in deck["ledger"] for f in row_figures(r)]
    homes: dict[str, list[tuple]] = {}
    for rule in RULES:
        home = _home(rule, deck["slides"])
        if home is not None:
            homes.setdefault(home, []).append(rule)
    asked: list[Figure] = []
    questions: list[dict] = []

    def add(slide: dict, rule: str, question: str, rows: list[dict], gap: dict | None, store: list[dict]) -> None:
        store.append(
            {
                "slide": slide["id"],
                "slide_title": slide["title"],
                "rule": rule,
                "question": question,
                "status": "gap" if gap else "answered",
                "answer": None if gap else draft_answer(rows),
                "gap": gap,
            }
        )

    def unknown_or(unknown: list[dict], text: str) -> str:
        return f"Ledger row {unknown[0]['id']} is Unknown." if unknown else text

    for slide in deck["slides"]:
        found: list[dict] = []
        due = gap_due

        # 1. The headline itself.
        rows, unknown = _headline_rows(slide, ledger)
        headline = f'What backs the headline: "{_clip(slide["title"])}"?'
        if rows:
            add(slide, "headline", headline, rows, None, found)
        else:
            why = unknown_or(unknown, "No ledger row holds the headline's figures." if figures(slide["title"]) else "No ledger row is cited on this slide.")
            add(slide, "headline", headline, [], {"what": why, "owner": gap_owner, "due": due}, found)

        # 2. Gaps the deck already declares.
        for need in slide["data_needed"]:
            add(
                slide,
                "data-needed",
                f"When will we see this: {_clip(need['text'], 120)}",
                [],
                {"what": need["text"], "owner": need.get("owner") or gap_owner, "due": need.get("due") or due},
                found,
            )

        # 3. Topic rules, each asked once in the deck, on its home slide.
        for rule, _trigger, question, topic in homes.get(slide["id"], []):
            rows, unknown = _pick_rows(slide, ledger, topic)
            if rows:
                add(slide, rule, question, rows, None, found)
            else:
                add(slide, rule, question, [], {"what": unknown_or(unknown, "No ledger row answers it."), "owner": gap_owner, "due": due}, found)

        # 4. Figures printed on the slide that no ledger row holds, each asked once in the deck.
        title_figs = figures(slide["title"])
        unsourced: list[dict] = []
        for fig in figures(slide["text"]):
            in_title = any(fig.matches(t) for t in title_figs)
            if not _worth_asking(fig, in_title) or any(fig.matches(a) for a in all_ledger_figs + asked):
                continue
            asked.append(fig)
            if len(unsourced) < MAX_UNSOURCED:
                what = f"{fig.text} is printed on slide {slide['id']} but no ledger row holds it."
                add(slide, "unsourced-figure", f"Where does {fig.text} come from?", [], {"what": what, "owner": gap_owner, "due": due}, unsourced)

        fixed = [q for q in found if q["rule"] in {"headline", "data-needed"}]
        topical = [q for q in found if q["rule"] not in {"headline", "data-needed"}]
        room = max(0, MAX_PER_SLIDE - len(fixed))
        questions.extend(fixed + topical[:room] + unsourced)

    numbered = [{"id": f"Q{i:02d}", **q} for i, q in enumerate(questions, start=1)]
    return {
        "deck": {
            "company": deck.get("company"),
            "period": deck.get("period"),
            "as_of": deck.get("as_of"),
            "cut": deck.get("cut"),
            "illustrative": deck.get("illustrative", False),
        },
        "ledger": deck["ledger"],
        "questions": numbered,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Draft likely board questions per slide, with ledger-cited answers or owned gaps.")
    p.add_argument("deck", help="Leader Report deck JSON, Markdown, or text saved from a PDF.")
    p.add_argument("--cut", default="B", help="Deck JSON only: B (board, default), L, S or all.")
    p.add_argument("--gap-owner", required=True, help="Who owns a gap the deck does not assign. A named person or role.")
    p.add_argument("--gap-due", help="When gaps are due, if the deck does not say.")
    p.add_argument("--out", default="qa.json")
    args = p.parse_args(argv)
    try:
        deck = deck_mod.load(args.deck, args.cut)
    except (deck_mod.DeckError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    qa = generate(deck, args.gap_owner, args.gap_due)
    Path(args.out).write_text(json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    answered = sum(q["status"] == "answered" for q in qa["questions"])
    total = len(qa["questions"])
    print(f"{total} questions across {len(deck['slides'])} slides: {answered} answered from the ledger, {total - answered} gaps. Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
