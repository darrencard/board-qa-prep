"""Find the figures in a piece of text and compare them, deterministically.

A figure is a number a reader would take as a claim: 41.2, $41.2M, 91.3%, 23.1K,
1,049, "9 of 11", "three". Labels are not figures and are removed first: ledger
references (L08), dates (30 Sep 2026, 2026-09-30, Sep 2026), years (2026), and
codes glued to letters (Q3, FY26, H1, Sev-2).

Each figure becomes a Figure(kind, value): kind is "pct" (a percent or points),
"money" (a currency amount) or "num". Two figures match when their kinds agree
and their values are equal after scaling (K, M, B, thousand, million, billion).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MONTHS = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
    r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b\.?"
)

# Removed before any figure is read. Order matters: refs and dates first.
_LABELS = [
    re.compile(r"\[\[?L\d+\]?\]"),  # [L08] or [[L08]]
    re.compile(r"\bL\d{1,3}\b"),  # bare ledger IDs
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),  # ISO dates
    re.compile(rf"\b\d{{1,2}}\s+{MONTHS}(?:\s+\d{{4}})?\b", re.IGNORECASE),  # 30 Sep 2026
    re.compile(rf"\b{MONTHS}\s+\d{{1,2}},?\s+\d{{4}}\b", re.IGNORECASE),  # Sep 30, 2026
    re.compile(rf"\b{MONTHS}\s+\d{{4}}\b", re.IGNORECASE),  # Sep 2026
    re.compile(r"\b(?:19|20)\d{2}\b(?![.,]\d)(?!\s*(?:%|percent))"),  # years
    re.compile(r"[A-Za-z]+-?\d+[A-Za-z]*"),  # Q3, FY26, H1, Sev-2, v0
]

_SCALE = {
    "k": 1e3,
    "thousand": 1e3,
    "m": 1e6,
    "mn": 1e6,
    "million": 1e6,
    "b": 1e9,
    "bn": 1e9,
    "billion": 1e9,
}

_FIGURE = re.compile(
    r"(?P<cur>[$£€])?\s?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"
    r"(?:\s?(?P<scale>thousand|million|billion|mn|bn|[kmb])\b)?"
    r"(?:\s?(?P<pct>%|percent\b|per cent\b|percentage points?\b|points?\b|pts?\b|pp\b))?",
    re.IGNORECASE,
)

# Spelled-out counts a reader takes as figures. "one" is left out: it is
# usually an article ("one decision"), not a claim.
_WORDS = {
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "half": 50,
    "dozen": 12,
    "doubled": 2,
    "tripled": 3,
}
_WORD_RE = re.compile(r"\b(" + "|".join(_WORDS) + r")\b", re.IGNORECASE)


@dataclass(frozen=True)
class Figure:
    kind: str  # "pct", "money" or "num"
    value: float
    text: str  # as written, for messages

    def matches(self, other: Figure) -> bool:
        if self.kind != other.kind:
            return False
        a, b = self.value, other.value
        return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def strip_labels(text: str) -> str:
    for pattern in _LABELS:
        text = pattern.sub(" ", text)
    return text


def figures(text: str | None) -> list[Figure]:
    """Every figure in the text, in order."""
    if not text:
        return []
    clean = strip_labels(str(text))
    found: list[Figure] = []
    for m in _FIGURE.finditer(clean):
        value = float(m.group("num").replace(",", ""))
        scale = (m.group("scale") or "").lower()
        value *= _SCALE.get(scale, 1.0)
        if m.group("pct"):
            kind = "pct"
        elif m.group("cur"):
            kind = "money"
        else:
            kind = "num"
        found.append(Figure(kind, value, m.group(0).strip()))
    for m in _WORD_RE.finditer(clean):
        word = m.group(1).lower()
        kind = "pct" if word == "half" else "num"
        # "Twenty-five" reads as 20 and 5, which no row holds: the check then asks for digits.
        found.append(Figure(kind, float(_WORDS[word]), m.group(1)))
    return found


def value_figures(value, unit) -> list[Figure]:
    """Figures for a ledger row's structured value and unit, if it has them."""
    if value is None or isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        unit_text = str(unit or "").strip().lower()
        if unit_text in {"%", "pct", "percent", "points", "pp"}:
            kind = "pct"
        elif unit_text in {"$", "usd", "gbp", "eur", "£", "€"}:
            kind = "money"
        else:
            kind = "num"
        return [Figure(kind, float(value), f"{value}{unit or ''}")]
    return figures(str(value))


def unmatched(answer: str, allowed: list[Figure]) -> list[Figure]:
    """Figures in the answer that no allowed figure matches."""
    return [f for f in figures(answer) if not any(f.matches(a) for a in allowed)]
