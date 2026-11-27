"""The Landing Loop record: one JSON file per bet, landing/<bet-slug>.json, shared by the loop's skills and the Leader Report.

board-qa-prep is step 05. It reads every key earlier in the record order and writes only its own key,
`board_qa`. Every other key is kept exactly as it was found. Every figure it writes carries value, unit,
source, window (from, to) and as_of.

Standard library only. Python 3.11 or later.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "landing-loop/1"
KEY = "board_qa"
# The record order (CONTRACT.md in landing-loop). A skill reads only keys earlier than its own.
ORDER = ("portfolio", "decisions", "spec", "release", "cost", "evals", "landed", "signals", "postmortem", "board_qa")
READS = ORDER[: ORDER.index(KEY)]
# The skill that writes each key, for "run X" in an open question.
WRITER = {
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
MAX_RECORD_BYTES = 2_000_000


class RecordError(ValueError):
    """A loop record that cannot be used. Nothing is written when this is raised."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dumps(record: dict[str, Any]) -> str:
    """The record as every loop skill writes it, so an unchanged key stays byte-identical."""
    return json.dumps(record, indent=2, ensure_ascii=False) + "\n"


def load(path: Path) -> dict[str, Any]:
    """The record, refused if it is not a landing-loop/1 record."""
    if not path.exists():
        raise RecordError(f"{path} does not exist. Run the earlier loop steps first, or point at landing/<bet>.json.")
    if path.stat().st_size > MAX_RECORD_BYTES:
        raise RecordError(f"{path} is over {MAX_RECORD_BYTES:,} bytes, so it is not a loop record.")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise RecordError(f"{path} is not valid JSON ({e}). It is left as it is.") from None
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        schema = record.get("schema") if isinstance(record, dict) else None
        raise RecordError(f"{path} is not a {SCHEMA} record (its schema is {schema!r}). It is left as it is.")
    if not isinstance(record.get("bet"), str) or not record["bet"]:
        raise RecordError(f"{path} names no bet. It is left as it is.")
    brief = record.get("brief")
    if not isinstance(brief, dict) or not brief.get("path"):
        raise RecordError(f"{path} has no brief path. Every loop record points at its landing brief.")
    return record


def brief_path(record_path: Path, record: dict[str, Any]) -> Path:
    """The brief, read relative to the working folder that holds landing/ (the record's own convention)."""
    p = Path(record["brief"]["path"])
    if p.is_absolute():
        return p
    folder = record_path.resolve().parent.parent
    return folder / p


def figure(value: Any, unit: str, source: str, window_from: str | None, window_to: str | None, as_of: str) -> dict[str, Any]:
    """One figure in the loop's shape. No figure without a source."""
    if not source:
        raise RecordError("a figure has no source. Every figure in the loop record needs one.")
    return {"value": value, "unit": unit, "source": source, "window": {"from": window_from, "to": window_to}, "as_of": as_of}


def is_figure(obj: Any) -> bool:
    return isinstance(obj, dict) and "value" in obj and "source" in obj


def get(record: dict[str, Any], path: str) -> Any:
    """The value at a path such as landed/figures/current, or None. Slashes, since keys such as pass_rate@v1.4 hold dots."""
    node: Any = record
    for part in path.split("/"):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def figures_in(obj: Any, prefix: str = "") -> list[tuple[str, dict[str, Any]]]:
    """Every figure-shaped entry inside a key, with its path, in the order the key holds them."""
    found: list[tuple[str, dict[str, Any]]] = []
    if is_figure(obj):
        return [(prefix, obj)]
    if isinstance(obj, dict):
        for k, v in obj.items():
            found += figures_in(v, f"{prefix}/{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found += figures_in(v, f"{prefix}/{i}")
    return found


def write(path: Path, record: dict[str, Any], board_qa: dict[str, Any]) -> Path:
    """Write the board_qa key and nothing else. Every other key is kept as it was read."""
    out = dict(record)
    out[KEY] = board_qa
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(dumps(out), encoding="utf-8")
    tmp.replace(path)
    return path
