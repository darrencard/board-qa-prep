# The project file answers 13 of 15 likely board questions. Two need an owner's answer before the meeting.

Board Q&A prep v0.3.2. As of 2026-11-26. Illustrative: every figure is invented.

Quote drafting is a project you expect to move a number. Its landing brief, a one-page plan, sets what good looks like, by when and at what cost. As the project moves from plan to board, each step adds its page to the project file. These are the questions a board will likely ask, each answered from that file with its source, or left open with a named owner. Code checks every figure.

**Project status, from did-it-land:** landed. 13 answered, 2 open.

## What to do next

Get an answer to Q15, "Is any customer data sent to the model provider?", from its owner before the meeting. Owner: Head of Product, Quoting squad. Due: before the board meeting.

## The five to prepare first

**Q15. Is any customer data sent to the model provider?** (open)

_Asked at the last meeting._

Nothing in the project file answers it, so it needs a person's answer. Owner: Head of Product, Quoting squad. Due: before the board meeting.

**Q02. Did it land?** (answered)

_Asked at the last meeting._

did-it-land says landed.

<details>
<summary>The full answer, with sources</summary>

Quote draft acceptance rate reads 43% [F02] to 2026-11-23, against a target of 40% [F03] by 2026-11-15. At the date it read 41% [F04]. The read also flags that cost is over budget.

</details>

**Q08. What does each task cost, against the budget?** (answered)

_Asked at the last meeting._

$0.0338 per task [F15] from 2026-11-01 to 2026-11-14, against a budget of $0.027 [F16]: over budget by 25% [F17].

<details>
<summary>The full answer, with sources</summary>

AI usage per task: 10,300 [F18] against 9,000 [F19]. AI price per unit: $0.00000328 [F20] against $0.000003 [F21]. The cost check computes these; the quality test cites the same cost per task.

</details>

**Q11. A failed check shipped on a named person's OK. Was it closed before that OK ran out?** (open)

Open bugs within the severity limits: shipped on the OK of Head of Product, Quoting squad, until 2026-09-19.

<details>
<summary>The full answer, with sources</summary>

No later release check in the project file says it closed. Owner: Lead, Quoting squad. Due: before the board meeting.

</details>

**Q03. Is the move real, or normal noise?** (answered)

Before launch the number averaged 21.7% [F05], with a spread of 3.83% [F06].

<details>
<summary>The full answer, with sources</summary>

By the date it sat 5.05 times that spread above the average [F07]. That rules out noise. It does not say what moved it: no comparison group held back is in the project file.

</details>

## The other 10

- Q01. What did we set out to do, and how will we know it worked? (answered)
- Q04. Did the result the number should move, move too? (answered)
- Q05. What did we decide, and who decided? (answered)
- Q06. Is quality holding as more of the work runs without a person? (answered)
- Q07. Is version 1.4 really better than version 1.3? (answered)
- Q09. Who brings cost back within budget, and by when? (answered)
- Q10. Was it ready to ship when it shipped? (answered)
- Q12. What are customers saying about it? (answered)
- Q13. What went wrong, and who owns each fix? (answered)
- Q14. Why this project, over the others? (answered)

<details>
<summary>The other 10 questions, answered or open</summary>

**Q01. What did we set out to do, and how will we know it worked?** (answered)

Tradespeople spend evenings writing quotes by hand, so quotes go out late and lose the job. The target: Quote draft acceptance rate at 40% or higher by 2026-11-15 [F01]. Head of Product, Quoting squad decides the next step.

**Q04. Did the result the number should move, move too?** (answered)

The result it should drive (Illustrative CRM export, quotes_won_weekly.csv) went from 31 [F08] on 2026-08-31 to 36 [F09] on 2026-11-23. It moved the same way as the number; the project file does not show why.

**Q05. What did we decide, and who decided?** (answered)

As of 2026-11-26: 5 decided [F10]. Set the undo trigger for quote drafting (Head of Product, Quoting squad, 2026-08-10); Choose the model tier for quote drafts (Tech lead, Quoting squad, 2026-08-10); Build quote drafting now, against its landing brief (Head of Product, Quoting squad, 2026-07-27).

**Q06. Is quality holding as more of the work runs without a person?** (answered)

Version 1.4's pass rate on test cases kept back is 80% [F11] on 30 cases [F13] (likely range 62.7% to 90.5%). 71.5% of tasks finished with no person [F12]. The quality test: not confirmed: too close to call. The rate itself meets the target, but the low end of the likely range does not clear it.

**Q07. Is version 1.4 really better than version 1.3?** (answered)

Pass rate on test cases kept back went from 70% [F14] on version 1.3 to 80% [F11] on version 1.4, on the same cases. The quality test marks the gain as too close to call for this case count, so it is not yet a proven gain.

**Q09. Who brings cost back within budget, and by when?** (answered)

The project file names the model behind most of it, the large model: $0.963 [F22] of $1.89 [F23] over budget. The after-action review names the fix: Send only drafts over the standard model's length limit to the large model, and route the rest back. Owner: Lead, Quoting squad, due 2026-12-10.

**Q10. Was it ready to ship when it shipped?** (answered)

release-readiness said ready to ship for Acme quote drafting version 1.0 on 2026-09-05: 6 [F24] of 7 [F25] checks ready to ship. Open bugs within the severity limits failed its check and shipped on the OK of Head of Product, Quoting squad, until 2026-09-19. Every spec-auditor hold was closed before release (undo plan, quality test plan).

**Q12. What are customers saying about it?** (answered)

customer-signal-digest says problem still raised. It read 21 signals [F26] from 16 accounts [F27] from 2026-09-07 to 2026-11-24. 7 signals [F28] from 7 accounts [F29] say the problem is still there. The top problem theme: Quote drafts miss line items.

**Q13. What went wrong, and who owns each fix?** (answered)

The learning review of 2026-11-26 covers 2 incidents [F30] from 2026-09-07 to 2026-11-26. Each change it lists cites its evidence. 4 fixes [F31], each with one owner and a due date: Send only drafts over the standard model's length limit to the large model, and route the rest back (Lead, Quoting squad, due 2026-12-10); Give every routing change made during an incident an end date, and list the open ones in the weekly incident review (Product manager, Quoting squad, due 2026-12-17); Put the cost check's result beside the quality test's result on every quote drafting release candidate (Tech lead, Quoting squad, due 2027-01-08); Show 'price updating' and retry when the price book sync lags, instead of price pending (Product manager, Quoting squad, due 2026-12-17).

**Q14. Why this project, over the others?** (answered)

The portfolio review ranked it 4 of 8 projects, 1 needs work first [F32] on 2026-07-27. Its brief scored 14 points of 14 [F33].

</details>

<details>
<summary>For your engineers</summary>

Skill: `board-qa-prep` 0.3.2.

| ID | Figure | Source | Window | As of |
|---|---|---|---|---|
| F01 | 40% | landing brief briefs/quote-drafting.md (landing_brief.py) | by 2026-11-15 | 2026-11-26 |
| F02 | 43% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-09-07 to 2026-11-23 | 2026-11-26 |
| F03 | 40% | landing brief: quote-drafting.md | by 2026-11-15 | 2026-11-26 |
| F04 | 41% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-09-07 to 2026-11-09 | 2026-11-26 |
| F05 | 21.7% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-07-27 to 2026-08-31 | 2026-11-26 |
| F06 | 3.83% | Illustrative product analytics export, quote_drafts_weekly.csv | 2026-07-27 to 2026-08-31 | 2026-11-26 |
| F07 | 5.05 sd | computed from Illustrative product analytics export, quote_drafts_weekly.csv | 2026-07-27 to 2026-11-09 | 2026-11-26 |
| F08 | 31 | Illustrative CRM export, quotes_won_weekly.csv | 2026-08-31 | 2026-11-26 |
| F09 | 36 | Illustrative CRM export, quotes_won_weekly.csv | 2026-08-31 to 2026-11-23 | 2026-11-26 |
| F10 | 5 decisions | decision-record 0.3.3: counted from decisions.md (sha256 096127d5d48d) | 2026-07-13 to 2026-11-26 | 2026-11-26 |
| F11 | 80% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-11-15 | 2026-11-15 |
| F12 | 71.5% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-11-15 | 2026-11-15 |
| F13 | 30 held-out cases | eval-kit 0.3.5: evals.rows, v1.4, cases | 2026-11-15 | 2026-11-15 |
| F14 | 70% | quote-drafting.csv (sha256 ee43a12a2395) | 2026-10-15 | 2026-11-15 |
| F15 | $0.0338 per task | cost-budget-check 0.3.3: priced cost / tasks; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F16 | $0.027 per task | landing brief quote-drafting.md (tokens per task x price per token) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F17 | 25% over budget | cost-budget-check 0.3.3: actual / budget - 1; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F18 | 10,300 tokens per task | cost-budget-check 0.3.3: tokens / tasks; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F19 | 9,000 tokens per task | landing brief quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F20 | $0.00000328 per token | cost-budget-check 0.3.3: priced cost / tokens; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15) | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F21 | $0.000003 per token | landing brief quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F22 | $0.963 | cost-budget-check 0.3.3: model cost - model token share x budgeted cost; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F23 | $1.89 | cost-budget-check 0.3.3: priced cost - tasks x budgeted cost per task; distinct task ids in gateway.jsonl; gateway.jsonl; pricing.json (Illustrative prices for the Acme sample. Not any provider's list price., retrieved 2026-10-15); quote-drafting.md | 2026-11-01 to 2026-11-14 | 2026-11-15 |
| F24 | 6 checks ready to ship | release-readiness 0.3.2: count of the checks above; examples/acme/inputs/release.json | 2026-09-05 | 2026-09-05 |
| F25 | 7 checks | release-readiness 0.3.2: count of the checks above; examples/acme/inputs/release.json | 2026-09-05 | 2026-09-05 |
| F26 | 21 signals | customer-signal-digest 0.3.2: signals in the window after duplicates were merged; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F27 | 16 accounts | customer-signal-digest 0.3.2: distinct accounts named on those signals; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F28 | 7 signals | customer-signal-digest 0.3.2: signals in themes on the problem side; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F29 | 7 accounts | customer-signal-digest 0.3.2: distinct accounts on the problem side; Zendesk: zendesk-page-1.json, zendesk-page-2.json; Intercom: intercom-conversations.json; CSV (calls): calls.csv; CSV (nps): nps.csv (illustrative) | 2026-09-07 to 2026-11-24 | 2026-11-26 |
| F30 | 2 incidents | PagerDuty (acme): PagerDuty incidents, created_at to resolved_at, services Quote drafting (pagerduty-incidents.json, retrieved 2026-11-26); incidents started in the window | 2026-09-07 to 2026-11-26 | 2026-11-26 |
| F31 | 4 fixes | review.json, checked by postmortem 0.3.2 | 2026-09-07 to 2026-11-26 | 2026-11-26 |
| F32 | 4 rank of 8 bets, 1 needs work first | bets.csv | 2026-07-27 | 2026-07-27 |
| F33 | 14 points of 14 | briefs/quote-drafting.md | 2026-07-27 | 2026-07-27 |

Read: portfolio, decisions, spec, release, cost, evals, landed, signals, postmortem. Not in the record yet: nothing.

board_qa.py adds its page to the project file: the `board_qa` key of `landing/<bet>.json`, and no other key.

</details>
