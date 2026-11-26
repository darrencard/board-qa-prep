# Check rules

`scripts/check.py` runs these on every question in `qa.json`. Any error blocks `render.py`.

| Code | What it catches | How to fix it |
|---|---|---|
| `figure-not-in-ledger` | A figure in an answer matches no figure in the rows it cites. The message names any other row that holds it. | Cite the row that holds it, or remove the figure, or make the question a gap. |
| `cite-missing` | An answered question cites no row. | Cite a row as `[L08]`, or make it a gap. |
| `cite-unknown-row` | An answer cites an ID the ledger does not have. | Cite a real row. |
| `cite-unknown-confidence` | An answer rests on a row whose confidence is Unknown. | Make it a gap. |
| `confidence-label-missing` | An answer cites an Estimated row and does not say "estimated". | Say it is an estimate. |
| `gap-no-owner` | A gap has no owner, or a placeholder (TBD, unassigned, unknown). | Name a person or a role. |
| `gap-has-answer` | A gap carries figures or citations in its answer. | Answer it from the ledger, or clear the answer. |
| `status-word` | "on track", "off track", "at risk", "green", "amber". | Use landed, watch or stalled. |
| `causal-claim` | "caused", "drove", "due to", "because of", "led to", "proves" and similar. | Say what moved and when, not why. |
| `bad-status` | `status` is not `answered` or `gap`. | Use one of the two. |
| `empty-question` | A question has no text. | Write the question. |
| `duplicate-id` | Two questions share an ID. | Give each its own. |

## How figures are matched

A figure is any number a reader would take as a claim: `41.2`, `$41.2M`, `91.3%`, `23.1K`, `1,049`, `3 points`, and the words two to twelve, twenty, dozen and half. Each has a kind (percent, money or a plain number) and a value after scaling (K, M, B, thousand, million, billion). A figure in an answer passes when a cited row holds one of the same kind and value, so `$41.2M` and `$41.2 million` match and `$41.3M` does not.

A row's figures come from its claim, its value and unit, its window and its source (so "376 of 412" in a source can be quoted).

Not figures, and removed before matching: ledger IDs (`L08`, `[L08]`, `[[L08]]`), dates (`30 Sep 2026`, `2026-09-30`, `Sep 2026`), years (`2026`), and codes glued to letters (`Q3`, `FY26`, `H1`, `Sev-2`). "One" is not read as a figure, since it is usually an article.
