# Changelog

## 0.3.0, 2026-11-26

- Step 05 of the Landing Loop. Reads the bet's `landing/<bet>.json` record (any of portfolio, decisions, spec, release, cost, evals, landed, signals and postmortem) and its landing brief, and writes only the `board_qa` key. Every other key stays byte-identical.
- Each likely question is answered, quoting the record's figure with its source, window and as_of, or open, with an owner (the brief's decider by default) and a due date. A key not yet in the record becomes an open question naming the skill to run.
- Landed, watch or stalled print only in the "Did it land?" answer, as `landed.status` holds them. The check blocks any other status word, any figure the cited record figures do not hold, and any causal claim.
- `edit` and `close` let Claude reword and record a named person's answer; both save only when the check passes.
- Sample: `examples/acme/board-qa-prep.html` in the Leader Report style, with a Markdown twin, rendered by `python3 examples/acme/sample.py` byte for byte. `--upstream` refreshes it from a fuller record.
- The brief parser and the report template are vendored byte-identical at a pinned commit (`VENDORED.json`).
- Removed: the deck reader from 0.1.0. The Leader Report reads the same record, so the board questions now start there.
- Python 3.11 or later.

## 0.1.0, 2026-11-26

- First version: questions per slide of a board deck, answered from the deck's evidence ledger, with a check on every figure. Private.
