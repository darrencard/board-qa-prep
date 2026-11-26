# Board questions answered from your ledger

A free Claude skill that reads your board deck, drafts the questions the board will likely ask on each slide, and answers each one only from your evidence ledger.

**Why it matters:** the hard board question is the one whose answer you cannot source. This skill finds those questions before the meeting, and names who owns each gap.

**How it works:** code reads the deck, drafts the questions and answers, and checks that every figure in every answer matches a ledger row the answer cites. Claude improves the wording; the checker blocks any figure it adds.

## Install: paste this into Claude Code

```text
Install the board-qa-prep skill from https://github.com/darrencard/board-qa-prep: clone the repository and copy skills/board-qa-prep into ~/.claude/skills/board-qa-prep. Run its tests with python3 -m unittest discover -s evals and show me the result. Then prepare me for board questions on my deck at PATH: ask me who owns gaps and by when, draft the likely questions per slide, answer each one only from the deck's evidence ledger, and show me the gaps first.
```

Replace `PATH` with your deck. It reads the [Product & Technology Leader Report](https://github.com/darrencard/product-engineering-update)'s deck JSON, or Markdown or text. For a PDF, Claude saves its text first and asks you to confirm the ledger it transcribed.

## What you get

- **Questions by slide.** The headline question for every slide, the gaps the deck already declares, one question per board topic (the decision, the gap to plan, quality next to speed, unit cost, AI margin, Finance reconciliation, risk, stop rules, hiring, impact), and "where does this number come from?" for every figure with no ledger row.
- **Answers that cite.** Each answer quotes ledger rows by ID, as `[L08]`, with their confidence, window and source.
- **Gaps with owners.** A question with no sourced answer is a gap with a named owner and a due date, listed first so you can chase them.
- **A check that blocks.** 12 rules, including any figure not in a cited row, an Unknown row used as an answer, an estimate not labelled, a cause the data does not show, and a status word other than landed, watch or stalled. See [the rules](skills/board-qa-prep/references/check-rules.md).

## Worked examples

Both companies are fictional and every figure is illustrative.

- [Harborline, board cut](examples/harborline.prep.md): from the Leader Report's sample deck.
- [Acme, Markdown deck](examples/acme.prep.md): invoicing software for trades businesses, from [a Markdown deck](evals/fixtures/acme-board.md).

## Run it by hand

```bash
python3 skills/board-qa-prep/scripts/run.py DECK --gap-owner "the CPTO" --gap-due "before the meeting" --out-dir prep
```

Python 3.9 or later, standard library only. Runs locally and makes no network calls. Tests: `python3 -m unittest discover -s evals`.

## Limits

It reads text, not PDF or slide files. It checks that answers are sourced, not that the ledger is right. Questions come from fixed rules, so Claude should add any a specific board would ask.

## Licence

MIT. Made by [Dacard](https://www.dacard.ai).
