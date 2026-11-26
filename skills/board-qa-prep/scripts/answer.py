"""Record an answer the user gives in conversation, then check it at once.

Two kinds:
  --text "..." with a ledger citation such as [L08]: a ledger answer.
  --text "..." --by "<name or role>": a stated answer, with no figures, from the
  person who gave it (who owns the gap to plan, what the ask is).

Never record an answer the user did not give. A figure must come from a ledger row.

Usage: python3 scripts/answer.py qa.json Q03 --text "..." [--by "<name>"]
Exit code 0 when the answer passes, 1 when it does not (nothing is written), 2 on bad input.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check import check  # noqa: E402


def apply(qa: dict, qid: str, text: str, by: str | None) -> tuple[dict, list[dict]]:
    out = copy.deepcopy(qa)
    q = next((q for q in out.get("questions") or [] if q.get("id") == qid), None)
    if q is None:
        raise KeyError(qid)
    q["status"] = "answered"
    q["answer"] = text
    q["stated_by"] = by
    q["gap"] = None
    problems = [p for p in check(out) if p["question"] == qid]
    return out, problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Record one answer the user gave, and check it before saving.")
    p.add_argument("qa")
    p.add_argument("question", help="Question ID, such as Q03.")
    p.add_argument("--text", required=True)
    p.add_argument("--by", help="Who stated a figure-free answer. A named person or role.")
    args = p.parse_args(argv)
    path = Path(args.qa)
    try:
        qa = json.loads(path.read_text(encoding="utf-8"))
        new, problems = apply(qa, args.question, args.text, args.by)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    except KeyError:
        print(f"error: no question {args.question} in {path}", file=sys.stderr)
        return 2
    if problems:
        print("Not saved:\n" + "\n".join(f"  {x['code']}: {x['message']}" for x in problems), file=sys.stderr)
        return 1
    path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {args.question}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
