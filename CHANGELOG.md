# Changelog

## 0.3.2, 2026-11-27

- Scorecard fix round: the frame shows the share bar and the 2 open questions; the 13 answered fold into a `<details>` inside the frame, whose rows keep the frame's columns (subgrid through `::details-content`, only inside `@supports selector(::details-content)`; elsewhere each folded row stacks, name and word on one line, the figure under it). The figure and word columns are fixed to the widest text in the frame, folded rows included, so opening the fold moves nothing. The share ("13 of 15 answered") and the owners' team ("Quoting squad", with the person mark) print once in the frame head, and each open row prints the owner's role only, with no wrap. A row with no picture gives its name the picture column too. The figure column prints in one case, numerals and capitals, as /update. Tests for each.
- The picture is scorecard rows in the grammar of the outcome scorecard on dacard.ai/update (svgkit 1.2.0, landing-loop 78784ef): a share bar first ("13 of 15" answered, "2 open"), then one row per likely question, open first with its due date, OPEN in ink and its owner in brass, then the answered ones by topic with the steps of the project file each reads and ANSWERED muted. Geist Mono 12px for labels and figures, Geist 14px for names, no text inside a picture, no box inside the frame. The tiles, their panel and the boxed check chips are gone; check words print as text.
- Cited check words in their skill's words: eval-kit's "not confirmed: too close to call" (an older project file's "inside noise" prints as it), and did-it-land's noise flag as "inside normal ups and downs".
- README and SKILL.md in plain words: project, target, the project file, the landing brief defined as a one-page plan. Keys, file names and flags are unchanged. SKILL.md uses the user's own word if they say bet.
- Tests from the rollout recipe: no text inside an SVG, no scaled SVG, labels 12px and names 14px, no box inside the frame, no legacy svgkit primitive (rendered with DeprecationWarning as an error), one frame with the share row then open then answered, brass only on open owners, the aria-label is the verdict, and the cited check words. The page's word budget is 650, as the rows print as text what the tiles drew inside an SVG.

## 0.3.1, 2026-11-27

- The HTML page follows the Landing Loop sample anatomy: the shared header (mark, DACARD, skill, date, version, blue Illustrative tag), the verdict as the heading ("The project file answers 13 of 15 likely board questions. Two need an owner's answer before the meeting."), the project's status from did-it-land, the signature picture, one next step (the first open question to prepare) with its owner in brass, then the five to prepare first beside the other ten in two columns.
- The long text folds behind the five to prepare first: each shows its point in one sentence, with the full answer and its sources in a fold. The other questions, the figures with their sources and the record key fold under "The other 10 questions" and "For your engineers". The Markdown twin folds the same way.
- The signature picture: one tile per question, answered (a quiet filled tile) or open (a brass outline with its owner), a dot on the five to prepare first. A 640 wide variant for desktop and a 340 wide one for phones; the aria-label states the answer. Drawn with svgkit, vendored byte-identical from landing-loop and pinned in `VENDORED.json` under `landing-loop`.
- Public copy in plain words, on the page and in the twin: project, target, landing brief (defined at first use), test cases kept back, the likely range, too close to call, the large model, AI usage per task, a named person's OK in place of a waiver. The record keeps its words, and the check reads those.
- The Illustrative tag is the family's blue, not the template's grey.
- Tests: the picture draws only printed figures, green appears only beside the word landed, the aria-label states the answer, public copy uses the plain words, and the vendored svgkit matches its pin.
- Design fix round 2: no text below 11px at any width (the page raises the vendored template's and svgkit's smaller sizes as it inlines them; the files on disk are unchanged); the header prints the plain name, Board Q&A prep, and the code name moves to the engineers' fold; public copy drops record, bet, the bar, PRD, ARR and tokens ("the project file"; "Nothing in the project file answers it"; the portfolio review by name); a legend line by the tiles, "● prepare first"; the heading keeps the family's standard gap.
- On phones up to 440px the picture's panel gives it its full 340px, so its 11px labels render at 11px at 390 and 375 wide.

## 0.3.0, 2026-11-26

- Step 05 of the Landing Loop. Reads the bet's `landing/<bet>.json` record (any of portfolio, decisions, spec, release, cost, evals, landed, signals and postmortem) and its landing brief, and writes only the `board_qa` key. Every other key stays byte-identical.
- Each likely question is answered, quoting the record's figure with its source, window and as_of, or open, with an owner (the brief's decider by default) and a due date. A key not yet in the record becomes an open question naming the skill to run.
- Landed, watch or stalled print only in the "Did it land?" answer, as `landed.status` holds them. The check blocks any other status word, any figure the cited record figures do not hold, and any causal claim.
- `edit` and `close` let Claude reword and record a named person's answer; both save only when the check passes.
- Sample: `examples/acme/board-qa-prep.html` in the Leader Report style, with a Markdown twin, rendered by `python3 examples/acme/sample.py` byte for byte. `--upstream` refreshes it from a fuller record.
- The brief parser and the report template are vendored byte-identical at a pinned commit (`VENDORED.json`).
- Reads the real shapes of the newer keys: decision-record's `rows` and `decided`, release-readiness's `readiness`, checks, waivers and `spec_holds`, customer-signal-digest's check word and themes, and the postmortem's `fixes` (one owner and a due date each). A postmortem fix that addresses the cost overrun answers who brings cost back within budget.
- Removed: the deck reader from 0.1.0. The Leader Report reads the same record, so the board questions now start there.
- Python 3.11 or later.
- The page opens with a one-line answer and a five-line summary (the questions to prepare first, one line each), then those five in full; the other questions, the record's keys and the ledger fold under `<details>`. The Markdown twin follows the same order.
- Check chips print in ink; brass is kept for an open question's owner and due date. Text selection and keyboard focus print in ink, not the template's green.
- Decisions: the most recent calls lead the decided list, and a record with no open decision rows reads cleanly.
- Every entry script stops on Python older than 3.11 before it reads or writes anything. The page renders before the record is written, and the sample builds in a scratch folder and moves its outputs into place only on success.

## 0.1.0, 2026-11-26

- First version: questions per slide of a board deck, answered from the deck's evidence ledger, with a check on every figure. Private.
