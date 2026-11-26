"""One command: read the deck, draft questions and answers, check, render.

Usage:
  python3 scripts/run.py DECK --gap-owner "<name or role>" [--gap-due DATE] [--cut B|L|S|all] [--out-dir prep]

Writes <out-dir>/qa.json and, when the check passes, <out-dir>/prep.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deck as deck_mod  # noqa: E402
from check import check, summary  # noqa: E402
from questions import generate  # noqa: E402
from render import render  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Board Q&A prep from a deck, in one step.")
    p.add_argument("deck")
    p.add_argument("--gap-owner", required=True)
    p.add_argument("--gap-due")
    p.add_argument("--cut", default="B")
    p.add_argument("--out-dir", default="prep")
    args = p.parse_args(argv)
    try:
        deck = deck_mod.load(args.deck, args.cut)
    except (deck_mod.DeckError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    qa = generate(deck, args.gap_owner, args.gap_due)
    (out / "qa.json").write_text(json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    problems = check(qa)
    print(summary(qa, problems))
    if problems:
        print(f"Not rendered. Fix {out / 'qa.json'} and run scripts/render.py.", file=sys.stderr)
        return 1
    (out / "prep.md").write_text(render(qa), encoding="utf-8")
    print(f"Wrote {out / 'qa.json'} and {out / 'prep.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
