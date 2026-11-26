import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import helpers
from answer import apply
from deck import load
from questions import generate


def gap_id(qa, rule):
    return next(q["id"] for q in qa["questions"] if q["rule"] == rule and q["status"] == "gap")


class AnswerTest(unittest.TestCase):
    """Recording answers the user gives. Acme and its figures are illustrative."""

    def setUp(self):
        self.qa = generate(load(helpers.ACME), "the CPTO", "20 Dec 2026")

    def test_stated_answer_closes_a_gap(self):
        qid = gap_id(self.qa, "decision")
        new, problems = apply(self.qa, qid, "Approve the routing work this meeting; without it the single provider stays.", "the CPTO")
        self.assertEqual(problems, [])
        q = next(q for q in new["questions"] if q["id"] == qid)
        self.assertEqual((q["status"], q["stated_by"], q["gap"]), ("answered", "the CPTO", None))

    def test_ledger_answer_with_wrong_figure_is_refused(self):
        qid = gap_id(self.qa, "plan")
        _, problems = apply(self.qa, qid, "ARR is $29M [L01].", None)
        self.assertEqual([p["code"] for p in problems], ["figure-not-in-ledger"])

    def test_cli_does_not_save_a_failing_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "qa.json"
            path.write_text(json.dumps(self.qa), encoding="utf-8")
            before = path.read_text(encoding="utf-8")
            qid = gap_id(self.qa, "plan")
            cmd = [sys.executable, str(helpers.SCRIPTS / "answer.py"), str(path), qid, "--text", "We expect 40% growth.", "--by", "the CPTO"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(res.returncode, 1)
            self.assertIn("stated-has-figure", res.stderr)
            self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_cli_saves_a_passing_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "qa.json"
            path.write_text(json.dumps(self.qa), encoding="utf-8")
            qid = gap_id(self.qa, "plan")
            cmd = [sys.executable, str(helpers.SCRIPTS / "answer.py"), str(path), qid, "--text", "The CFO owns the expansion plan review.", "--by", "the CFO"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(res.returncode, 0, res.stderr)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(next(q for q in saved["questions"] if q["id"] == qid)["status"], "answered")


if __name__ == "__main__":
    unittest.main()
