# Board questions, answered from the record

```text
Install the board-qa-prep skill from https://github.com/darrencard/board-qa-prep: clone it, find a Python 3.11 or later on this machine (macOS python3 is often 3.9), run python examples/acme/sample.py with it, and copy skills/board-qa-prep into ~/.claude/skills/board-qa-prep. Then prepare me for board questions on my bet: find its landing/<bet>.json record, ask me who owns open questions and by when, and for the questions the board asked last time. Show me the five to prepare first, then walk me through each open question.
```

A free Claude skill that lists the questions a board will likely ask about one bet: each answered from the Landing Loop record with its source, or open with an owner.

**Why it matters:** the hard board question is the one you cannot source. This finds those before the meeting and names who owes each answer.

**Where it sits:** step 05 (Report) of the Landing Loop. It reads the bet's `landing/<bet>.json` record, writes only its `board_qa` key, and renders one HTML page in the Leader Report style.

**How it works:** Python drafts every question, answer and figure from the record. Claude may reword; a check blocks any figure, status word or cause the record does not hold.

## Try it on Acme

Acme is invented: invoicing software for trades businesses. Every figure is illustrative. From a fresh clone, Python 3.11 or later, nothing to install:

```bash
python3 examples/acme/sample.py
```

It rewrites [examples/acme/board-qa-prep.html](examples/acme/board-qa-prep.html), its Markdown twin and the `board_qa` key of [examples/acme/landing/quote-drafting.json](examples/acme/landing/quote-drafting.json), byte for byte as committed (a test checks this). The bet is quote drafting, bar "quote draft acceptance rate at 40% or higher by 2026-11-15". The page opens with a one-line answer and the five questions to prepare first, one line each; the rest is folded below. From the page:

```text
**Q02. Did it land?** (answered)

did-it-land says landed. Quote draft acceptance rate reads 43% [F02] to 2026-11-23, against a bar of 40% [F03] by 2026-11-15. At the date it read 41% [F04].
```

The sample reads the full record, every key from portfolio to postmortem, and marks each question answered from the record or open with an owner. Decisions come from decision-record's open rows and decided list, the release from release-readiness's readiness word, waivers and spec holds, customers from customer-signal-digest's problem still raised or problem not raised, and fixes from the postmortem's one owner and due date per fix. When the loop record changes, one command refreshes the input and the sample:

```bash
python3 examples/acme/sample.py --upstream ../landing-loop/examples/acme/landing/quote-drafting.json
```

## Install

In Claude Code:

```text
/plugin marketplace add darrencard/landing-loop
/plugin install board-qa-prep@landing-loop
```

Standalone: clone this repository and copy `skills/board-qa-prep` into `~/.claude/skills/`. Run it by hand:

```bash
python3 skills/board-qa-prep/scripts/board_qa.py prep landing/<bet>.json --past past-questions.md --html board-qa.html --md board-qa.md
```

## Reads and writes

| | |
|---|---|
| Reads | `landing/<bet>.json`: any of portfolio, decisions, spec, release, cost, evals, landed, signals, postmortem (every key before `board_qa` in the loop's order). The landing brief, through the loop's shared parser, vendored byte-identical. Optional: last meeting's questions, one per line or a CSV with a `question` column. |
| Writes | Only the `board_qa` key. Every other key stays byte-identical. Plus one self-contained HTML page and its Markdown twin. |
| Data in | The record is built from live data by the earlier steps (PostHog, Amplitude, Stripe, AI gateways, through the Leader Report's collectors). This step reads no source of its own, so it needs no keys. Past questions come from minutes: paste them, or save them from Drive or Notion as text. |
| Words | Each question is answered or open. Landed, watch or stalled print only as did-it-land set them. |

## The record key

```json
"board_qa": {
  "tool": "board-qa-prep 0.3.0",
  "as_of": "2026-11-26",
  "read": ["portfolio", "decisions", "spec", "release", "cost", "evals", "landed", "signals", "postmortem"],
  "not_in_record": [],
  "first": ["Q17", "Q02", "Q05", "Q07", "Q10"],
  "questions": [
    {"id": "Q07", "topic": "decision-open", "question": "Which decisions are still open, and who makes them?", "check": "open",
     "missing": "From decision-record, as of 2026-07-27: 2 open [F11], 1 past due [F12]. ...",
     "owner": "Lead, Quoting squad", "due": "before the board meeting"}
  ],
  "figures": {
    "F11": {"value": 2, "unit": "decisions", "source": "decision-record 0.3.0: counted from decisions.md (sha256 42c46365e3dc)",
            "window": {"from": "2026-07-13", "to": "2026-07-27"}, "as_of": "2026-07-27", "from": "decisions/figures/open"}
  }
}
```

Each figure is copied from the record with the path it came from, so any answer traces back to the skill that computed it. [SKILL.md](skills/board-qa-prep/SKILL.md) has every question rule; [check-rules.md](skills/board-qa-prep/references/check-rules.md) has every check.

## Limits

- It does not check that the record is right. A wrong upstream figure gives a wrong answer that passes.
- Questions come from fixed rules over the record. A board's own concerns (people, security, the market) arrive only through last meeting's questions or you.
- Past questions are placed on a topic by shared words, nothing cleverer. Check the topic each one was given.
- Not yet run on a real team's data.

## Licence

MIT. Made by [Dacard](https://www.dacard.ai). Python 3.11 or later, standard library only, no network calls. Tests: `python3 -m unittest discover -s evals`.

Claude and Claude Code are trademarks of Anthropic, PBC. These skills are independent and not affiliated with or endorsed by Anthropic.
