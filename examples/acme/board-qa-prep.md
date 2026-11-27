# Board questions: Quote drafting

As of 2026-11-26. board-qa-prep 0.3.0. Step 05 Report. Illustrative: every figure is invented.

**13 of 17 likely questions are answered from the loop record; 4 need an answer from their owner before the meeting.**

- Q17. Is any customer data sent to the model provider? (open, owner Head of Product, Quoting squad, due before the board meeting)
- Q02. Did it land? (answered from the record)
- Q05. Do we scale it, and who decides? (open, owner Head of Product, Quoting squad, due before the board meeting)
- Q07. Which decisions are still open, and who makes them? (open, owner Lead, Quoting squad, due before the board meeting)
- Q10. What does each task cost, against the budget? (answered from the record)

17 questions: 13 answered from the record, 4 open with an owner. Bet status, from did-it-land: landed.

## Prepare these first

**Q17. Is any customer data sent to the model provider?** (open)

_Asked at the last meeting._

Nothing in the record answers it, so it needs a person's answer. Owner: Head of Product, Quoting squad. Due: before the board meeting.

**Q02. Did it land?** (answered)

_Asked at the last meeting._

did-it-land says landed. Quote draft acceptance rate reads 43% [F02] to 2026-11-23, against a bar of 40% [F03] by 2026-11-15. At the date it read 41% [F04].

**Q05. Do we scale it, and who decides?** (open)

did-it-land's next step: Keep the metric on the scorecard, and decide whether to scale the bet. The decision record was last updated 2026-07-27, before did-it-land's read, so it holds no call on this yet: run decision-record. Owner: Head of Product, Quoting squad. Due: before the board meeting.

**Q07. Which decisions are still open, and who makes them?** (open)

From decision-record, as of 2026-07-27: 2 open [F11], 1 past due [F12]. Set the rollback trigger for quote drafting (Lead, Quoting squad, due 2026-08-03); Choose the model tier for quote drafts (Tech lead, Quoting squad, due 2026-08-03). No later decision record says they closed. Owner: Lead, Quoting squad. Due: before the board meeting.

**Q10. What does each task cost, against the budget?** (answered)

_Asked at the last meeting._

$0.0338 per task [F17] from 2026-11-01 to 2026-11-14, against a budget of $0.027 [F18]: over budget by 25% [F19]. Tokens per task: 10,300 [F20] against 9,000 [F21]. Price per token: $0.00000328 [F22] against $0.000003 [F23]. cost-budget-check computes these; eval-kit cites the same cost per task.

<details>
<summary>The rest: open and answered questions, and every figure with its source</summary>

## Open, with an owner

**Q13. Was the waived check closed before its waiver ran out?** (open)

Open bugs within the severity limits: waived by Head of Product, Quoting squad until 2026-09-19. No later release check in the record says it closed. Owner: Lead, Quoting squad. Due: before the board meeting.

## Answered from the record

**Q01. What did we bet on, and how will we know it worked?** (answered)

Tradespeople spend evenings writing quotes by hand, so quotes go out late and lose the job. The bar: Quote draft acceptance rate at 40% or higher by 2026-11-15 [F01]. Head of Product, Quoting squad decides the next step.

**Q03. Is the move real, or normal noise?** (answered)

Before launch the metric averaged 22.2% [F05], with a spread of 0.75% [F06]. By the date it sat 25 spreads above that mean [F07]. That rules out noise. It does not say what moved it: no holdout group is in the record.

**Q04. Did the result the metric should move, move too?** (answered)

The outcome series (Illustrative CRM export, quotes_won_weekly.csv) went from 31 [F08] on 2026-08-31 to 36 [F09] on 2026-11-23. It moved the same way as the metric; the record does not show why.

**Q06. What did we decide, and who decided?** (answered)

From decision-record, as of 2026-07-27: 3 decided [F10]. Build quote drafting now, against its landing brief (Head of Product, Quoting squad, 2026-07-27); Quote drafts wait for the tradesperson's approval before they send (Head of Product, Quoting squad, 2026-07-27); Prices come from the price book, never the model (Tech lead, Quoting squad, 2026-07-27).

**Q08. Is quality holding as more of the work runs without a person?** (answered)

v1.4's held-out pass rate is 80% [F13] on 30 cases [F15] (95% interval 62.7% to 90.5%). 71.5% of tasks finished with no person [F14]. eval-kit's build check: meets target.

**Q09. Is v1.4 really better than v1.3?** (answered)

Held-out pass rate went from 70% [F16] on v1.3 to 80% [F13] on v1.4, on the same cases. eval-kit marks the gain as inside the noise for this case count, so it is not yet a proven gain.

**Q11. Who brings cost back within budget, and by when?** (answered)

The record names the model behind most of it, vendor-a/xl: $0.963 [F24] of $1.89 [F25] over budget. The postmortem names the fix: Send only drafts over the standard model's context limit to vendor-a/xl, and route the rest back. Owner: Lead, Quoting squad, due 2026-12-10.

**Q12. Was it ready to ship when it shipped?** (answered)

release-readiness said ready to ship for Acme quote drafting v1.0 on 2026-09-05: 6 [F26] of 7 [F27] checks ready to ship. Open bugs within the severity limits read hold under a waiver from Head of Product, Quoting squad until 2026-09-19. Every spec-auditor hold was closed before release (rollback, eval-plan).

**Q14. What are customers saying about it?** (answered)

customer-signal-digest says problem still raised. It read 21 signals [F28] from 16 accounts [F29] from 2026-09-07 to 2026-11-24. 7 signals [F30] from 7 accounts [F31] say the problem is still there. The top problem theme: Quote drafts miss line items.

**Q15. What went wrong, and who owns each fix?** (answered)

The learning review of 2026-11-26 covers 2 incidents [F32] from 2026-09-07 to 2026-11-26. Each change it lists cites its evidence. 4 fixes [F33], each with one owner and a due date: Send only drafts over the standard model's context limit to vendor-a/xl, and route the rest back (Lead, Quoting squad, due 2026-12-10); Give every routing change made during an incident an end date, and list the open ones in the weekly incident review (Platform on-call lead, due 2026-12-17); Put the cost-budget-check result beside the eval-kit result on every quote drafting release candidate (Tech lead, Quoting squad, due 2027-01-08); Show 'price updating' and retry when the price book sync lags, instead of price pending (Price book squad lead, due 2026-12-17).

**Q16. Why this bet, over the others?** (answered)

bet-portfolio-review ranked it 4 of 8 bets, 1 needs work first [F34] on 2026-07-27. Its brief scored 14 points of 14 [F35].

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
| F10 | 3 decisions | decision-record 0.3.0: counted from decisions.md (sha256 a01557cce6fe) | 2026-07-13 to 2026-07-27 | 2026-07-27 |
| F11 | 2 decisions | decision-record 0.3.0: counted from decisions.md (sha256 a01557cce6fe) | 2026-07-13 to 2026-07-27 | 2026-07-27 |
| F12 | 1 decisions | decision-record 0.3.0: counted from decisions.md (sha256 a01557cce6fe) | 2026-07-13 to 2026-07-27 | 2026-07-27 |
| F13 | 80% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-11-15 | 2026-11-15 |
| F14 | 71.5% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-11-15 | 2026-11-15 |
| F15 | 30 held-out cases | eval-kit 0.3.3: evals.rows, v1.4, cases | 2026-11-15 | 2026-11-15 |
| F16 | 70% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-10-15 | 2026-11-15 |
| F17 | $0.0338 per task | cost-budget-check 0.3.1: priced cost / tasks; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F18 | $0.027 per task | landing brief quote-drafting.md (tokens per task x price per token) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F19 | 25% over budget | cost-budget-check 0.3.1: actual / budget - 1; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F20 | 10,300 tokens per task | cost-budget-check 0.3.1: tokens / tasks; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F21 | 9,000 tokens per task | landing brief quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F22 | $0.00000328 per token | cost-budget-check 0.3.1: priced cost / tokens; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F23 | $0.000003 per token | landing brief quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F24 | $0.963 | cost-budget-check 0.3.1: model cost - model token share x budgeted cost; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F25 | $1.89 | cost-budget-check 0.3.1: priced cost - tasks x budgeted cost per task; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F26 | 6 checks ready to ship | release-readiness 0.3.0: count of the checks above; examples/acme/inputs/release.json | 2026-09-05 | 2026-09-05 |
| F27 | 7 checks | release-readiness 0.3.0: count of the checks above; examples/acme/inputs/release.json | 2026-09-05 | 2026-09-05 |
| F28 | 21 signals | customer-signal-digest 0.3.0: signals in the window after duplicates were merged; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F29 | 16 accounts | customer-signal-digest 0.3.0: distinct accounts named on those signals; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F30 | 7 signals | customer-signal-digest 0.3.0: signals in themes on the problem side; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F31 | 7 accounts | customer-signal-digest 0.3.0: distinct accounts on the problem side; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F32 | 2 incidents | PagerDuty (acme): PagerDuty incidents, created_at to resolved_at, services Quote drafting (pagerduty-incidents.json, retrieved 2026-11-26); incidents started in the window | 2026-09-07 to 2026-11-26 | 2026-11-26 |
| F33 | 4 fixes | review.json, checked by postmortem 0.3.0 | 2026-09-07 to 2026-11-26 | 2026-11-26 |
| F34 | 4 rank of 8 bets, 1 needs work first | bets.csv | 2026-07-27 | 2026-07-27 |
| F35 | 14 points of 14 | briefs/quote-drafting.md | 2026-07-27 | 2026-07-27 |

Not in the record yet: nothing.

</details>
