# Board questions: Quote drafting

As of 2026-11-26. board-qa-prep 0.3.0. Step 05 Report. Illustrative: every figure is invented.

13 questions: 8 answered from the record, 5 open with an owner. Bet status, from did-it-land: landed.

## Prepare these first

**Q13. Is any customer data sent to the model provider?** (open)

_Asked at the last meeting._

Nothing in the record answers it, so it needs a person's answer. Owner: Head of Product, Quoting squad. Due: before the board meeting.

**Q02. Did it land?** (answered)

_Asked at the last meeting._

did-it-land says landed. Quote draft acceptance rate reads 43% [F02] to 2026-11-23, against a bar of 40% [F03] by 2026-11-15. At the date it read 41% [F04].

**Q05. Do we scale it, and who decides?** (open)

did-it-land's next step: Keep the metric on the scorecard, and decide whether to scale the bet. No decision is recorded yet: run decision-record. Owner: Head of Product, Quoting squad. Due: before the board meeting.

**Q08. What does each task cost, against the budget?** (answered)

_Asked at the last meeting._

$0.0338 per task [F14] from 2026-11-01 to 2026-11-14, against a budget of $0.027 [F15]: over budget by 25% [F16]. Tokens per task: 10,300 [F17] against 9,000 [F18]. Price per token: $0.00000328 [F19] against $0.000003 [F20]. cost-budget-check computes these; eval-kit cites the same cost per task.

**Q09. Who brings cost back within budget, and by when?** (open)

The record names the model behind most of it, vendor-a/xl: $0.963 [F21] of $1.89 [F22] over budget. It holds no plan and no owner for the fix. Owner: Head of Product, Quoting squad. Due: before the board meeting.

## Open, with an owner

**Q10. Were the spec's holds fixed before it shipped?** (open)

spec-auditor held the spec on 2 findings [F23] on 2026-08-03: The rollback plan has no trigger threshold. The eval plan has no time it runs. No later audit or release check is in the record: run release-readiness. Owner: Head of Product, Quoting squad. Due: before the board meeting.

**Q11. What are customers saying about it?** (open)

Not in the record yet: run customer-signal-digest. Owner: Head of Product, Quoting squad. Due: before the board meeting.

## Answered from the record

**Q01. What did we bet on, and how will we know it worked?** (answered)

Tradespeople spend evenings writing quotes by hand, so quotes go out late and lose the job. The bar: Quote draft acceptance rate at 40% or higher by 2026-11-15 [F01]. Head of Product, Quoting squad decides the next step.

**Q03. Is the move real, or normal noise?** (answered)

Before launch the metric averaged 22.2% [F05], with a spread of 0.75% [F06]. By the date it sat 25 spreads above that mean [F07]. That rules out noise. It does not say what moved it: no holdout group is in the record.

**Q04. Did the result the metric should move, move too?** (answered)

The outcome series (Illustrative CRM export, quotes_won_weekly.csv) went from 31 [F08] on 2026-08-31 to 36 [F09] on 2026-11-23. It moved the same way as the metric; the record does not show why.

**Q06. Is quality holding as more of the work runs without a person?** (answered)

v1.4's held-out pass rate is 80% [F10] on 30 cases [F12] (95% interval 62.7% to 90.5%). 71.5% of tasks finished with no person [F11]. eval-kit's build check: meets target.

**Q07. Is v1.4 really better than v1.3?** (answered)

Held-out pass rate went from 70% [F13] on v1.3 to 80% [F10] on v1.4, on the same cases. eval-kit marks the gain as inside the noise for this case count, so it is not yet a proven gain.

**Q12. Why this bet, over the others?** (answered)

bet-portfolio-review ranked it 4 of 8 bets, 1 needs work first [F24] on 2026-07-27. Its brief scored 14 points of 14 [F25].

## Ledger

| ID | Figure | Source | Window | As of |
|---|---|---|---|---|
| F01 | 40% | landing brief briefs/quote-drafting.md (landing_brief.py) | by 2026-11-15 | 2026-11-26 |
| F02 | 43% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-09-07 to 2026-11-23 | 2026-11-26 |
| F03 | 40% | landing brief: quote-drafting.md | by 2026-11-15 | 2026-11-26 |
| F04 | 41% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-09-07 to 2026-11-09 | 2026-11-26 |
| F05 | 22.2% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-07-27 to 2026-08-31 | 2026-11-26 |
| F06 | 0.75% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-07-27 to 2026-08-31 | 2026-11-26 |
| F07 | 25 sd | computed from Illustrative product analytics export, quote_drafts_weekly.csv | 2026-07-27 to 2026-11-09 | 2026-11-26 |
| F08 | 31 | Illustrative CRM export, quotes_won_weekly.csv | 2026-08-31 | 2026-11-26 |
| F09 | 36 | Illustrative CRM export, quotes_won_weekly.csv | 2026-08-31 to 2026-11-23 | 2026-11-26 |
| F10 | 80% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-11-15 | 2026-11-15 |
| F11 | 71.5% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-11-15 | 2026-11-15 |
| F12 | 30 held-out cases | eval-kit 0.3.2: evals.rows, v1.4, cases | 2026-11-15 | 2026-11-15 |
| F13 | 70% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-10-15 | 2026-11-15 |
| F14 | $0.0338 per task | cost-budget-check 0.3.0: priced cost / tasks; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F15 | $0.027 per task | landing brief quote-drafting.md (tokens per task x price per token) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F16 | 25% over budget | cost-budget-check 0.3.0: actual / budget - 1; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F17 | 10,300 tokens per task | cost-budget-check 0.3.0: tokens / tasks; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F18 | 9,000 tokens per task | landing brief quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F19 | $0.00000328 per token | cost-budget-check 0.3.0: priced cost / tokens; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F20 | $0.000003 per token | landing brief quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F21 | $0.963 | cost-budget-check 0.3.0: model cost - model token share x budgeted cost; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F22 | $1.89 | cost-budget-check 0.3.0: priced cost - tasks x budgeted cost per task; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F23 | 2 findings | spec-auditor 0.3.0, audit of examples/acme/specs/quote-drafting.md | 2026-08-03 | 2026-08-03 |
| F24 | 4 rank of 8 bets, 1 needs work first | bets.csv | 2026-07-27 | 2026-07-27 |
| F25 | 14 points of 14 | briefs/quote-drafting.md | 2026-07-27 | 2026-07-27 |

Not in the record yet: decisions, release, signals, postmortem.
