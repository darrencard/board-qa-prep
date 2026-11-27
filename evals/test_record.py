"""The Landing Loop record: board-qa-prep reads every earlier key, writes only board_qa, and sources every figure."""

import contextlib
import copy
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

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

    def test_open_questions_name_the_brief_owner_by_default(self):
        opens = [q for q in self.key["questions"] if q["check"] == "open"]
        self.assertTrue(opens)
        for q in opens:
            self.assertEqual(q["owner"], "Head of Product, Quoting squad")
            self.assertEqual(q["due"], "before the board meeting")

    def test_cost_over_budget_opens_a_question_for_an_owner(self):
        self.assertEqual(self.by_topic["cost"][0]["check"], "answered")
        self.assertIn("over budget", self.by_topic["cost"][0]["answer"])
        self.assertEqual(self.by_topic["cost-owner"][0]["check"], "open")

    def test_missing_keys_say_which_skill_to_run(self):
        self.assertEqual(self.key["not_in_record"], ["decisions", "release", "signals", "postmortem"])
        self.assertIn("run decision-record", self.by_topic["decision"][0]["missing"])
        self.assertIn("run customer-signal-digest", self.by_topic["signals"][0]["missing"])

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

    def test_full_record_with_the_new_keys(self):
        r = upstream()
        r["decisions"] = {
            "tool": "decision-record 0.3.0",
            "as_of": "2026-11-20",
            "decisions": [{"title": "Scale quote drafting to all plans", "owner": "Head of Product", "status": "open", "due": "2026-12-10"}],
        }
        r["release"] = {"tool": "release-readiness 0.3.0", "as_of": "2026-09-05", "verdict": "ready to ship"}
        r["signals"] = {
            "tool": "customer-signal-digest 0.3.0",
            "as_of": "2026-11-25",
            "figures": {"mentions": loop.figure(42, "mentions", "Illustrative support export", "2026-11-01", "2026-11-24", "2026-11-25")},
        }
        r["postmortem"] = {
            "tool": "postmortem 0.3.0",
            "as_of": "2026-11-22",
            "fixes": [{"fix": "Cap the xl model to long quotes", "owner": "Quoting squad lead", "status": "open"}],
        }
        rec = self.run_with({k: r[k] for k in ("schema", "bet", "brief", *loop.READS) if k in r})
        key = rec["board_qa"]
        self.assertEqual(key["not_in_record"], [])
        topics = {q["topic"]: q for q in key["questions"]}
        self.assertEqual(topics["decision"]["check"], "open")
        self.assertEqual(topics["decision"]["owner"], "Head of Product")
        self.assertIn("ready to ship", topics["release"]["answer"])
        self.assertIn("42", topics["signals"]["answer"])
        self.assertEqual(topics["postmortem"]["owner"], "Quoting squad lead")
        self.assertEqual(check.check(rec), [])

    def test_stalled_bet_asks_for_a_postmortem(self):
        r = upstream()
        r["landed"] = copy.deepcopy(r["landed"])
        r["landed"]["status"] = "stalled"
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
