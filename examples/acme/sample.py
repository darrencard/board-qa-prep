#!/usr/bin/env python3
"""Regenerate the committed Acme sample: board-qa-prep.html, board-qa-prep.md and the board_qa key of landing/quote-drafting.json.

Inputs, all illustrative (Acme is an invented company): the canonical brief in briefs/ (copied from the
landing-loop repo, unchanged), the questions the board asked last time in inputs/, and upstream/quote-drafting.json,
the loop record as the earlier steps left it (copied unchanged from landing-loop). The same inputs give the same
bytes, so a chain script can call this and a test can check it.

Usage, from the repo root:
  python3 examples/acme/sample.py [--into DIR]
  python3 examples/acme/sample.py --upstream ~/landing-loop/examples/acme/landing/quote-drafting.json

--upstream first refreshes upstream/quote-drafting.json from a newer loop record, keeping only the keys
board-qa-prep reads (every key before board_qa in the record order), then regenerates the sample. It refuses a
record whose brief hash differs from briefs/quote-drafting.md. --into writes the outputs somewhere else (the
test uses it).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

if sys.version_info < (3, 11):  # noqa: UP036  (the floor, checked before anything is read or written)
    sys.exit("board-qa-prep needs Python 3.11 or later; try python3.12")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skills" / "board-qa-prep" / "scripts"))

import board_qa  # noqa: E402
import loop  # noqa: E402

BET = "quote-drafting"
AS_OF = "2026-11-26"


def refresh(src: Path) -> list[str]:
    record = loop.load(src)
    if record["bet"] != BET:
        raise SystemExit(f"{src} is the record for {record['bet']!r}, not {BET!r}.")
    if record["brief"].get("sha256") != loop.sha256(HERE / "briefs" / f"{BET}.md"):
        raise SystemExit(f"{src} reads a different brief from briefs/{BET}.md. Copy the brief again first.")
    kept = {k: record[k] for k in ("schema", "bet", "brief")} | {k: record[k] for k in loop.READS if k in record}
    staged = HERE / "upstream" / f"{BET}.json.tmp"
    staged.write_text(loop.dumps(kept), encoding="utf-8")
    staged.replace(HERE / "upstream" / f"{BET}.json")
    return [k for k in loop.READS if k in record]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--into", type=Path, help="output folder (default examples/acme)")
    p.add_argument("--upstream", type=Path, help="a newer loop record to read from (default upstream/quote-drafting.json)")
    args = p.parse_args(argv)
    if args.upstream:
        print("upstream: " + ", ".join(refresh(args.upstream.expanduser())))
    into = args.into.resolve() if args.into else HERE
    with tempfile.TemporaryDirectory() as tmp:
        # Build in a scratch folder and move the outputs into place only on success, so a failed run never leaves
        # the committed record stripped back to its upstream keys.
        work = Path(tmp)
        shutil.copytree(HERE / "briefs", work / "briefs")
        record = work / "landing" / f"{BET}.json"
        record.parent.mkdir()
        # Start from the record as the earlier steps left it: board-qa-prep reads them all and writes only board_qa.
        shutil.copy(HERE / "upstream" / f"{BET}.json", record)
        code = board_qa.main(
            [
                "prep", str(record),
                "--past", str(HERE / "inputs" / "past-questions.md"),
                "--as-of", AS_OF,
                "--html", str(work / "board-qa-prep.html"),
                "--md", str(work / "board-qa-prep.md"),
            ]
        )  # fmt: skip
        if code == 0:
            if into != HERE:
                shutil.copytree(HERE / "briefs", into / "briefs", dirs_exist_ok=True)
            (into / "landing").mkdir(parents=True, exist_ok=True)
            for name in ("board-qa-prep.html", "board-qa-prep.md", f"landing/{BET}.json"):
                staged = into / f"{name}.tmp"
                shutil.copy(work / name, staged)
                staged.replace(into / name)
    if code == 0:
        print(f"sample: wrote board-qa-prep.html, board-qa-prep.md and landing/{BET}.json to {into}")
    return code


if __name__ == "__main__":
    sys.exit(main())
