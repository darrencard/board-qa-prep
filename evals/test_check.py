"""The check: the model may reword, but never add a figure or a status word the record does not hold."""

import contextlib
import copy
import io
import json
import re
import unittest

from _path import ACME

# isort: split
import board_qa
import check
from figures import figures
from test_record import PAST, Work

RECORD = json.loads((ACME / "landing" / "quote-drafting.json").read_text(encoding="utf-8"))


def q(rec: dict, topic: str) -> dict:
    return next(x for x in rec["board_qa"]["questions"] if x["topic"] == topic)


def codes(rec: dict) -> set[str]:
    return {e["code"] for e in check.check(rec)}


class Rules(unittest.TestCase):
    def setUp(self):
        self.rec = copy.deepcopy(RECORD)

    def test_the_committed_sample_passes(self):
        self.assertEqual(check.check(self.rec), [])

    def test_a_figure_the_record_does_not_hold_is_blocked(self):
        q(self.rec, "landed")["answer"] = "did-it-land says landed. Acceptance is 45% [F02]."
        self.assertIn("figure-not-cited", codes(self.rec))

    def test_a_rounded_figure_is_blocked(self):
        q(self.rec, "cost")["answer"] = "About $0.03 per task [F14]."
        self.assertIn("figure-not-cited", codes(self.rec))

    def test_a_figure_without_its_citation_is_blocked(self):
        q(self.rec, "cost")["answer"] = "Cost per task is $0.0338."
        self.assertIn("figure-not-cited", codes(self.rec))

    def test_citing_a_figure_that_is_not_there(self):
        q(self.rec, "cost")["answer"] = "Cost per task is $0.0338 [F99]."
        self.assertIn("cite-unknown", codes(self.rec))

    def test_status_word_outside_its_rule(self):
        q(self.rec, "cost")["answer"] = "Cost has stalled."
        self.assertIn("status-word", codes(self.rec))
        self.rec = copy.deepcopy(RECORD)
        q(self.rec, "landed")["answer"] = "did-it-land says watch."
        self.assertIn("status-word", codes(self.rec))
        self.rec = copy.deepcopy(RECORD)
        q(self.rec, "quality")["answer"] = "Quality is on track."
        self.assertIn("status-word", codes(self.rec))

    def test_status_words_print_only_where_the_rule_allows(self):
        for x in RECORD["board_qa"]["questions"]:
            for field in ("question", "answer", "missing"):
                found = check.BET_STATUS.findall(str(x.get(field) or ""))
                if found:
                    self.assertEqual((x["topic"], field, {w.lower() for w in found}), ("landed", "answer", {RECORD["landed"]["status"]}))

    def test_causal_claim_is_blocked(self):
        q(self.rec, "outcome")["answer"] = "Quotes won rose because of the assistant."
        self.assertIn("causal-claim", codes(self.rec))

    def test_open_needs_a_real_owner(self):
        x = next(x for x in self.rec["board_qa"]["questions"] if x["check"] == "open")
        x["owner"] = "TBD"
        self.assertIn("open-no-owner", codes(self.rec))

    def test_only_two_check_words(self):
        q(self.rec, "cost")["check"] = "partly"
        self.assertIn("check-word", codes(self.rec))

    def test_a_changed_record_figure_is_caught(self):
        self.rec["board_qa"]["figures"]["F02"]["value"] = 45.0
        self.assertIn("figure-changed", codes(self.rec))

    def test_figures_ignore_versions_dates_and_ids(self):
        self.assertEqual(figures("v1.4 on 2026-11-15, board-qa-prep 0.3.0 [F01] Q03"), [])


class EditAndClose(unittest.TestCase):
    def setUp(self):
        self.w = Work()
        self.w.prep("--past", str(PAST))

    def tearDown(self):
        self.w.close()

    def run_cmd(self, *args: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return board_qa.main([args[0], str(self.w.path), *args[1:]])

    def ids(self, topic: str) -> str:
        return q(self.w.record(), topic)["id"]

    def test_a_reword_that_keeps_the_figures_is_saved(self):
        qid = self.ids("cost")
        cost, budget = re.findall(r"\[F\d+\]", q(self.w.record(), "cost")["answer"])[:2]
        text = f"Each quote costs $0.0338 {cost}, against a budget of $0.027 {budget}: over budget."
        self.assertEqual(self.run_cmd("edit", qid, "--answer", text), 0)
        self.assertEqual(q(self.w.record(), "cost")["answer"], text)

    def test_a_reword_that_adds_a_figure_is_not_saved(self):
        before = self.w.path.read_text(encoding="utf-8")
        self.assertEqual(self.run_cmd("edit", self.ids("cost"), "--answer", "Each quote costs 3 cents."), 1)
        self.assertEqual(self.w.path.read_text(encoding="utf-8"), before)

    def test_close_records_a_stated_answer_and_recounts(self):
        qid = self.ids("past")
        was_open = self.w.record()["board_qa"]["counts"]["open"]["value"]
        self.assertEqual(self.run_cmd("close", qid, "--text", "No. Quote text goes to the provider with names removed.", "--by", "the CTO"), 0)
        rec = self.w.record()
        x = q(rec, "past")
        self.assertEqual((x["check"], x["stated_by"]), ("answered", "the CTO"))
        self.assertNotIn("owner", x)
        self.assertEqual(rec["board_qa"]["counts"]["open"]["value"], was_open - 1)
        self.assertEqual(check.check(rec), [])

    def test_close_refuses_a_figure_and_a_placeholder_name(self):
        qid = self.ids("past")
        self.assertEqual(self.run_cmd("close", qid, "--text", "Only 2% of quotes leave the country.", "--by", "the CTO"), 1)
        self.assertEqual(self.run_cmd("close", qid, "--text", "No.", "--by", "TBD"), 1)
        self.assertEqual(q(self.w.record(), "past")["check"], "open")


if __name__ == "__main__":
    unittest.main()
