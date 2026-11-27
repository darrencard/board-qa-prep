"""The Landing Loop record: board-qa-prep reads every earlier key, writes only board_qa, and sources every figure."""

import contextlib
import copy
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _path import ACME

# isort: split
import board_qa
import check
import loop

UPSTREAM = ACME / "upstream" / "quote-drafting.json"
PAST = ACME / "inputs" / "past-questions.md"


class Work:
    """A working folder holding briefs/ and landing/<bet>.json, as a user's would."""

    def __init__(self, record: dict | None = None):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        shutil.copytree(ACME / "briefs", self.dir / "briefs")
        self.path = self.dir / "landing" / "quote-drafting.json"
        self.path.parent.mkdir()
        if record is None:
            shutil.copy(UPSTREAM, self.path)
        else:
            self.path.write_text(loop.dumps(record), encoding="utf-8")

    def prep(self, *extra: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return board_qa.main(["prep", str(self.path), "--as-of", "2026-11-26", *extra])

    def record(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def close(self):
        self.tmp.cleanup()


def upstream() -> dict:
    return json.loads(UPSTREAM.read_text(encoding="utf-8"))


class WritesOnlyItsKey(unittest.TestCase):
    def setUp(self):
        self.w = Work()

    def tearDown(self):
        self.w.close()

    def test_read_keys_stay_byte_identical(self):
        before = upstream()
        self.assertEqual(self.w.prep("--past", str(PAST)), 0)
        after = self.w.record()
        self.assertEqual(set(after) - set(before), {"board_qa"})
        for k in before:
            self.assertEqual(json.dumps(after[k], indent=2, ensure_ascii=False), json.dumps(before[k], indent=2, ensure_ascii=False), k)

    def test_the_file_minus_board_qa_is_the_upstream_file(self):
        self.w.prep()
        after = self.w.record()
        del after["board_qa"]
        self.assertEqual(loop.dumps(after), UPSTREAM.read_text(encoding="utf-8"))

    def test_a_rerun_replaces_only_board_qa(self):
        self.w.prep()
        first = self.w.path.read_text(encoding="utf-8")
        self.w.prep()
        self.assertEqual(self.w.path.read_text(encoding="utf-8"), first)

    def test_reads_only_keys_earlier_in_the_order(self):
        self.assertEqual(loop.READS, ("portfolio", "decisions", "spec", "release", "cost", "evals", "landed", "signals", "postmortem"))
        self.assertEqual(loop.ORDER[-1], "board_qa")


class FiguresCarryTheirSource(unittest.TestCase):
    def setUp(self):
        self.w = Work()
        self.w.prep("--past", str(PAST))
        self.rec = self.w.record()
        self.key = self.rec["board_qa"]

    def tearDown(self):
        self.w.close()

    def test_every_figure_has_the_loop_shape(self):
        figs = list(self.key["figures"].items()) + [(f"counts.{k}", v) for k, v in self.key["counts"].items()]
        self.assertGreater(len(figs), 20)
        for name, f in figs:
            for field in ("value", "unit", "source", "window", "as_of"):
                self.assertIn(field, f, name)
            self.assertTrue(f["source"], name)
            self.assertEqual(set(f["window"]), {"from", "to"}, name)

    def test_copied_figures_match_the_record(self):
        for fid, f in self.key["figures"].items():
            if f["from"].startswith(("brief/", "evals/rows/")):
                continue
            there = loop.get(self.rec, f["from"])
            self.assertEqual((there["value"], there["source"], there["window"]), (f["value"], f["source"], f["window"]), fid)

    def test_every_answer_figure_is_cited(self):
        self.assertEqual(check.check(self.rec), [])

    def test_counts_add_up(self):
        c = {k: v["value"] for k, v in self.key["counts"].items()}
        self.assertEqual(c["answered"] + c["open"], c["questions"])
        self.assertEqual(c["questions"], len(self.key["questions"]))


class TheAcmeRead(unittest.TestCase):
    def setUp(self):
        self.w = Work()
        self.w.prep("--past", str(PAST))
        self.key = self.w.record()["board_qa"]
        self.by_topic = {}
        for q in self.key["questions"]:
            self.by_topic.setdefault(q["topic"], []).append(q)

    def tearDown(self):
        self.w.close()

    def test_landed_is_printed_from_did_it_land(self):
        q = self.by_topic["landed"][0]
        self.assertEqual(q["check"], "answered")
        self.assertIn("did-it-land says landed", q["answer"])

    def test_open_questions_name_the_owner_the_record_gives(self):
        up = upstream()
        opens = {q["topic"]: q for q in self.key["questions"] if q["check"] == "open"}
        expected = {"past", "release"} | ({"decision-open"} if up["decisions"].get("rows") else set())
        self.assertLessEqual(expected, set(opens))
        self.assertLessEqual(set(opens), expected | {"decision"})
        self.assertEqual(opens["past"]["owner"], "Head of Product, Quoting squad")
        if "decision" in opens:
            self.assertEqual(opens["decision"]["owner"], "Head of Product, Quoting squad")
        if "decision-open" in opens:
            self.assertEqual(opens["decision-open"]["owner"], up["decisions"]["rows"][0]["owner"])
        self.assertEqual(opens["release"]["owner"], "Lead, Quoting squad")
        for q in opens.values():
            self.assertEqual(q["due"], "before the board meeting")

    def test_every_owner_is_an_acme_org_chart_role(self):
        roles = {"Head of Product, Quoting squad", "Lead, Quoting squad", "Tech lead, Quoting squad", "Product manager, Quoting squad"}
        self.assertLessEqual({q["owner"] for q in self.key["questions"] if q["check"] == "open"}, roles)

    def test_cost_over_budget_is_answered_by_the_postmortem_fix(self):
        self.assertEqual(self.by_topic["cost"][0]["check"], "answered")
        self.assertIn("over budget", self.by_topic["cost"][0]["answer"])
        owner = self.by_topic["cost-owner"][0]
        self.assertEqual(owner["check"], "answered")
        self.assertIn("Owner: Lead, Quoting squad, due 2026-12-10.", owner["answer"])
        self.assertEqual(owner["from_keys"], ["cost", "postmortem"])

    def test_every_key_before_board_qa_is_read(self):
        self.assertEqual(self.key["read"], list(loop.READS))
        self.assertEqual(self.key["not_in_record"], [])

    def test_decisions_are_read_from_rows_and_decided(self):
        dec = upstream()["decisions"]
        made = self.by_topic["decision-made"][0]
        self.assertEqual(made["check"], "answered")
        self.assertIn(f"{len(dec['decided'])} decided", made["answer"])
        latest = sorted(dec["decided"], key=lambda x: x["date"], reverse=True)[0]
        self.assertIn(f"{latest['title']} ({latest['decided_by']}, {latest['date']})", made["answer"])
        if dec["rows"]:
            still = self.by_topic["decision-open"][0]
            self.assertIn(f"{len(dec['rows'])} open", still["missing"])
            first = dec["rows"][0]
            self.assertIn(f"{first['ask']} ({first['owner']}, due {first['deadline']})", still["missing"])
        else:
            self.assertNotIn("decision-open", self.by_topic)

    def test_evals_print_the_build_word_with_its_interval(self):
        ev = upstream()["evals"]
        q = self.by_topic["quality"][0]
        self.assertEqual(q["check"], "answered")
        self.assertEqual(ev["status"], "not confirmed: inside noise")
        lo, hi = ev["figures"][f"pass_rate@{ev['version']}"]["interval_95"]
        self.assertIn(f"(95% interval {lo}% to {hi}%)", q["answer"])
        self.assertIn("eval-kit's build check: not confirmed: inside noise.", q["answer"])
        self.assertNotIn("meets target", q["answer"])

    def test_release_reads_readiness_waivers_and_spec_holds(self):
        shipped, waived = self.by_topic["release"]
        self.assertEqual(shipped["check"], "answered")
        self.assertIn("release-readiness said ready to ship for Acme quote drafting v1.0 on 2026-09-05", shipped["answer"])
        self.assertIn("read hold under a waiver from Head of Product, Quoting squad until 2026-09-19", shipped["answer"])
        self.assertIn("Every spec-auditor hold was closed before release (rollback, eval-plan).", shipped["answer"])
        self.assertEqual(waived["check"], "open")
        self.assertNotIn("spec", self.by_topic)

    def test_signals_print_the_digest_check_word(self):
        q = self.by_topic["signals"][0]
        self.assertEqual(q["check"], "answered")
        self.assertTrue(q["answer"].startswith("customer-signal-digest says problem still raised."))
        self.assertIn("The top problem theme: Quote drafts miss line items.", q["answer"])

    def test_postmortem_names_one_owner_and_due_date_per_fix(self):
        q = self.by_topic["postmortem"][0]
        self.assertEqual(q["check"], "answered")
        for fix in upstream()["postmortem"]["fixes"]:
            self.assertIn(f"{fix['owner']}, due {fix['due']}", q["answer"])

    def test_past_questions_land_on_their_topic_or_open(self):
        asked = [q for q in self.key["questions"] if q.get("asked_last_time")]
        self.assertEqual(sorted(q["topic"] for q in asked), ["cost", "landed", "past"])
        past = self.by_topic["past"][0]
        self.assertEqual(past["check"], "open")
        self.assertEqual(past["question"], "Is any customer data sent to the model provider?")
        self.assertEqual(self.key["first"][0], past["id"])

    def test_brief_is_read_by_the_shared_parser(self):
        self.assertEqual(self.key["brief"], {"path": "briefs/quote-drafting.md", "complete": True, "problems": [], "unchanged": True})


class AnyRecordInTheContract(unittest.TestCase):
    """Keys the loop is still building: the code must read them when they arrive, and say so when they do not."""

    def run_with(self, record: dict) -> dict:
        w = Work(record)
        try:
            self.assertEqual(w.prep(), 0)
            return w.record()
        finally:
            w.close()

    def test_brief_only_record(self):
        r = {k: upstream()[k] for k in ("schema", "bet", "brief")}
        key = self.run_with(r)["board_qa"]
        self.assertEqual(key["read"], [])
        self.assertEqual(key["questions"][0]["check"], "answered")
        self.assertEqual(next(q for q in key["questions"] if q["topic"] == "landed")["check"], "open")

    def test_record_before_the_new_keys_says_which_skill_to_run(self):
        r = {k: v for k, v in upstream().items() if k not in ("decisions", "release", "signals", "postmortem")}
        key = self.run_with(r)["board_qa"]
        self.assertEqual(key["not_in_record"], ["decisions", "release", "signals", "postmortem"])
        topics = {q["topic"]: q for q in key["questions"]}
        self.assertIn("No decision is recorded yet: run decision-record.", topics["decision"]["missing"])
        self.assertIn("run release-readiness", topics["spec"]["missing"])
        self.assertIn("run customer-signal-digest", topics["signals"]["missing"])
        self.assertEqual(topics["cost-owner"]["check"], "open")

    def test_held_release_quiet_problem_and_unowned_fix(self):
        r = copy.deepcopy(upstream())
        r["release"]["readiness"] = "hold"
        r["release"]["checks"][0]["readiness"] = "hold"
        r["signals"]["check"] = "problem not raised"
        r["postmortem"]["fixes"][1]["owner"] = "TBD"
        rec = self.run_with(r)
        key = rec["board_qa"]
        topics: dict = {}
        for q in key["questions"]:
            topics.setdefault(q["topic"], []).append(q)
        holding = next(q for q in topics["release"] if q["question"].startswith("What is holding"))
        self.assertEqual((holding["check"], holding["owner"]), ("open", "Tech lead, Quoting squad"))
        self.assertIn("CI passes on the release commit", holding["missing"])
        self.assertTrue(topics["signals"][0]["answer"].startswith("customer-signal-digest says problem not raised."))
        self.assertNotIn("say the problem is still there", topics["signals"][0]["answer"])
        self.assertEqual(topics["postmortem"][0]["check"], "open")
        self.assertIn("No single owner and due date for: Give every routing change", topics["postmortem"][0]["missing"])
        self.assertEqual(check.check(rec), [])

    def test_stalled_bet_asks_for_a_postmortem(self):
        r = upstream()
        r["landed"] = copy.deepcopy(r["landed"])
        r["landed"]["status"] = "stalled"
        del r["postmortem"]
        key = self.run_with(r)["board_qa"]
        self.assertIn("run postmortem", next(q for q in key["questions"] if q["topic"] == "postmortem")["missing"])

    def test_a_changed_brief_is_an_open_question(self):
        r = upstream()
        r["brief"] = {**r["brief"], "sha256": "0" * 64}
        key = self.run_with(r)["board_qa"]
        self.assertFalse(key["brief"]["unchanged"])
        self.assertTrue(any("brief changed" in q["question"] for q in key["questions"]))

    def test_not_a_loop_record_is_refused(self):
        w = Work({"schema": "something-else", "bet": "quote-drafting", "brief": {"path": "x"}})
        try:
            self.assertEqual(w.prep(), 2)
            self.assertNotIn("board_qa", w.record())
        finally:
            w.close()


if __name__ == "__main__":
    unittest.main()


class DecisionsMade(unittest.TestCase):
    """decision-record's record as of 2026-11-26: 5 decided, 0 open. The reader leaves no decision question open that it answers."""

    def setUp(self):
        self.up = upstream()
        self.w = Work(self.up)

    def tearDown(self):
        self.w.close()

    def test_no_open_rows_reads_cleanly_and_leads_with_the_latest_calls(self):
        dec = self.up["decisions"]
        self.assertEqual(dec["rows"], [])
        self.assertEqual((dec["figures"]["open"]["value"], dec["figures"]["decided"]["value"]), (0, 5))
        self.assertEqual(dec["figures"]["waiting_long"]["value"], 0)
        self.assertIn("usual_days_to_decide", dec["figures"])
        self.assertIn("days_to_decide@D-0004", dec["figures"])
        html, md = self.w.dir / "p.html", self.w.dir / "p.md"
        self.assertEqual(self.w.prep("--past", str(PAST), "--html", str(html), "--md", str(md)), 0)
        rec = self.w.record()
        key = rec["board_qa"]
        self.assertEqual(check.check(rec), [])
        topics = {q["topic"]: q for q in key["questions"]}
        self.assertNotIn("decision-open", topics)
        self.assertNotIn("decision", topics)  # the record is as of did-it-land's read, so it answers the scale call
        made = topics["decision-made"]
        self.assertEqual(made["check"], "answered")
        self.assertTrue(made["answer"].split(": ", 1)[1].startswith("5 decided"), made["answer"])
        self.assertIn("Set the rollback trigger for quote drafting (Head of Product, Quoting squad, 2026-08-10)", made["answer"])
        self.assertIn("Choose the model tier for quote drafts (Tech lead, Quoting squad, 2026-08-10)", made["answer"])
        self.assertIn(made["id"], html.read_text(encoding="utf-8"))
        # The twin prints the record's words in plain words: the rollback trigger is the undo trigger.
        self.assertIn("Set the undo trigger for quote drafting", md.read_text(encoding="utf-8"))

    def test_a_record_older_than_the_read_keeps_the_scale_call_open(self):
        rec = copy.deepcopy(self.up)
        rec["decisions"]["as_of"] = "2026-08-10"
        w = Work(rec)
        try:
            self.assertEqual(w.prep(), 0)
            topics = {q["topic"]: q for q in w.record()["board_qa"]["questions"]}
            self.assertEqual(topics["decision"]["check"], "open")
            self.assertEqual(topics["decision"]["owner"], "Head of Product, Quoting squad")
        finally:
            w.close()


class FailureSafe(unittest.TestCase):
    def test_a_render_failure_writes_nothing(self):
        w = Work()
        try:
            before = w.path.read_bytes()
            with mock.patch.object(board_qa.render_html, "page", side_effect=TypeError("boom")), self.assertRaises(TypeError):
                w.prep("--html", str(w.dir / "p.html"))
            self.assertEqual(w.path.read_bytes(), before)
            self.assertFalse((w.dir / "p.html").exists())
        finally:
            w.close()
