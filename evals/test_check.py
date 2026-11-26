import copy
import unittest

import helpers  # noqa: F401
from check import check

LEDGER = [
    {"id": "L01", "claim": "ARR $28.4M", "value": None, "unit": None, "source": "Billing", "window": "30 Sep 2026", "confidence": "Verified"},
    {"id": "L02", "claim": "Deploys per week up 30% against Q2", "source": "GitHub", "window": "Q3 FY26", "confidence": "Estimated"},
    {"id": "L03", "claim": "Inference cost by segment", "source": None, "window": None, "confidence": "Unknown"},
    {"id": "L04", "claim": "Eval pass rate 88.5%", "source": "Eval harness, 354 of 400", "window": "Run of 27 Sep 2026", "confidence": "Verified"},
]


def qa(answer=None, status="answered", gap=None):
    return {
        "ledger": copy.deepcopy(LEDGER),
        "questions": [{"id": "Q01", "slide": "1", "question": "Where is ARR?", "status": status, "answer": answer, "gap": gap}],
    }


def codes(doc):
    return [p["code"] for p in check(doc)]


class CheckTest(unittest.TestCase):
    def test_clean_answer_passes(self):
        self.assertEqual(codes(qa("ARR closed at $28.4M on 30 Sep 2026 [L01].")), [])

    def test_figure_from_source_or_window_counts(self):
        self.assertEqual(codes(qa("88.5% passed, 354 of 400 cases [L04].")), [])

    def test_invented_figure_is_blocked(self):
        self.assertEqual(codes(qa("ARR closed at $28.4M, up 22% [L01].")), ["figure-not-in-ledger"])

    def test_changed_figure_is_blocked(self):
        self.assertEqual(codes(qa("ARR closed at $28.5M [L01].")), ["figure-not-in-ledger"])

    def test_figure_from_an_uncited_row_is_blocked_with_a_hint(self):
        problems = check(qa("ARR closed at $28.4M and evals passed 88.5% [L01]."))
        self.assertEqual([p["code"] for p in problems], ["figure-not-in-ledger"])
        self.assertIn("L04", problems[0]["message"])

    def test_answer_needs_a_citation(self):
        self.assertEqual(codes(qa("ARR is healthy.")), ["cite-missing"])

    def test_unknown_row_id(self):
        self.assertEqual(codes(qa("See [L99].")), ["cite-unknown-row"])

    def test_unknown_confidence_cannot_answer(self):
        self.assertEqual(codes(qa("Segment cost is tracked [L03].")), ["cite-unknown-confidence"])

    def test_estimated_must_say_so(self):
        self.assertEqual(codes(qa("Deploys per week rose 30% [L02].")), ["confidence-label-missing"])
        self.assertEqual(codes(qa("Estimated: deploys per week rose 30% [L02].")), [])

    def test_status_vocabulary(self):
        self.assertEqual(codes(qa("ARR is on track at $28.4M [L01].")), ["status-word"])

    def test_causal_claim(self):
        self.assertEqual(codes(qa("Evals drove ARR to $28.4M [L01].")), ["causal-claim"])

    def test_gap_needs_a_named_owner(self):
        for owner in [None, "", "TBD", "unassigned"]:
            self.assertEqual(codes(qa(status="gap", gap={"what": "No row", "owner": owner})), ["gap-no-owner"], owner)
        self.assertEqual(codes(qa(status="gap", gap={"what": "No row", "owner": "the CFO"})), [])

    def test_gap_cannot_carry_a_figure_answer(self):
        doc = qa("Probably about $2M.", status="gap", gap={"what": "No row", "owner": "the CFO"})
        self.assertEqual(codes(doc), ["gap-has-answer"])

    def test_stated_answer_without_figures_passes(self):
        doc = qa("The platform squad owns the routing work and reports back next meeting.")
        doc["questions"][0]["stated_by"] = "the VP Engineering"
        self.assertEqual(codes(doc), [])

    def test_stated_answer_cannot_carry_a_figure(self):
        doc = qa("Routing should save 20% of inference.")
        doc["questions"][0]["stated_by"] = "the VP Engineering"
        self.assertEqual(codes(doc), ["stated-has-figure"])

    def test_stated_answer_needs_a_name(self):
        doc = qa("The platform squad owns it.")
        doc["questions"][0]["stated_by"] = "TBD"
        self.assertEqual(codes(doc), ["stated-no-name"])

    def test_stated_answer_still_cannot_claim_a_cause(self):
        doc = qa("Routing work drove the improvement.")
        doc["questions"][0]["stated_by"] = "the CPTO"
        self.assertEqual(codes(doc), ["causal-claim"])

    def test_bad_status_and_duplicates(self):
        self.assertEqual(codes(qa("x", status="maybe")), ["bad-status"])
        doc = qa("ARR $28.4M [L01].")
        doc["questions"].append(dict(doc["questions"][0]))
        self.assertEqual(codes(doc), ["duplicate-id"])


if __name__ == "__main__":
    unittest.main()
