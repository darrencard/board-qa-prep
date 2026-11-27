"""How a record figure reads on the page: its value from its value and unit, never in scientific notation.

The drafting code writes answers with these strings and the check allows exactly these strings, so a
reworded answer can keep a figure only as the record holds it.

Standard library only. Python 3.11 or later.
"""

from __future__ import annotations

import math
from typing import Any


def sig(v: float, n: int = 3) -> str:
    """A number to n significant figures, never in scientific notation: 0.00000328, 0.0338, 10,300."""
    v = float(v)
    if v == 0:
        return "0"
    if v.is_integer() and abs(v) >= 1:
        return f"{int(v):,}"
    d = max(0, n - 1 - math.floor(math.log10(abs(v))))
    s = f"{v:,.{d}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def num(f: dict[str, Any]) -> str:
    """A figure's value as a reader sees it, from its value and unit: 43%, $0.0338, 10,300, 25%."""
    v, unit = f.get("value"), str(f.get("unit") or "").lower()
    if not isinstance(v, int | float) or isinstance(v, bool):
        return str(v)
    if unit.startswith("%") or unit == "percent":
        return f"{sig(v)}%"
    if unit.startswith("share"):
        return f"{sig(v * 100, 2)}%"
    if unit.startswith("usd") or unit == "$":
        return f"${sig(v)}"
    return sig(v)
