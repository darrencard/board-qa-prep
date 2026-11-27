# Check rules

`scripts/check.py` runs these on the `board_qa` key. Any error blocks `prep`, `edit`, `close` and `render` from saving or drawing.

| Code | What it catches | How to fix it |
|---|---|---|
| `figure-not-cited` | A number in a question, answer or missing line matches no figure the text cites. | Cite the record figure as `[F01]`, exactly as the page shows it, or remove the number. |
| `cite-unknown` | The text cites an ID the key does not hold. | Cite a real figure. |
| `figure-shape` | A figure lacks value, unit, source, window (from, to) or as_of, or its source is empty. | Every figure needs all five. |
| `figure-changed` | A figure copied from the record no longer matches the record at its `from` path. | Run `prep` again; never edit a figure by hand. |
| `check-word` | `check` is not answered or open. | Use one of the two. |
| `open-no-owner` | An open question has no owner, or a placeholder (TBD, unassigned, unknown). | Name a person or a role. |
| `open-no-missing` | An open question does not say what is missing. | Say what the record lacks. |
| `answered-no-source` | An answered question cites no figure, names no record key and is not a stated answer. | Cite a figure, or save what a person said with `close --by`. |
| `stated-no-name` | A stated answer's `stated_by` is a placeholder. | Name who said it. |
| `status-word` | Landed, watch or stalled anywhere but the "Did it land?" answer, or one that differs from `landed.status`; or on track, off track, at risk, green, amber, RAG. | A bet's status is did-it-land's word. A question is answered or open. |
| `causal-claim` | caused, drove, due to, because of, led to, proves and similar, in an answer or missing line. | Say what moved and when, not why. |
| `empty-question` | A question has no text. | Write the question. |
| `duplicate-id` | Two questions share an ID. | Give each its own. |

## How figures are matched

A figure is any number a reader would take as a claim: `43%`, `$0.0338`, `10,300`, `2 findings`, and the words two to twenty, the tens, hundred, dozen, half, doubled and tripled. A cited figure allows its value as the page shows it (from its value and unit: a share shows as a percent, USD with a dollar sign, never in scientific notation), any number in its unit (`of 8 bets`), and its 95% interval when it has one. So `$0.0338 [F14]` passes and `about 3 cents [F14]` does not.

Not figures, and removed first: figure IDs (`[F01]`), versions (`v1.4`, `0.3.0`), dates (`2026-11-15`, `15 Nov 2026`), years, and codes glued to letters (`Q3`, `FY26`).
