import unittest

import helpers  # noqa: F401
from figures import Figure, figures, unmatched, value_figures


def kinds(text):
    return [(f.kind, f.value) for f in figures(text)]


class FiguresTest(unittest.TestCase):
    def test_money_scales(self):
        self.assertEqual(kinds("ARR $41.2M"), [("money", 41_200_000.0)])
        self.assertEqual(kinds("Inference $612K"), [("money", 612_000.0)])
        self.assertEqual(kinds("$1.2 billion"), [("money", 1_200_000_000.0)])

    def test_percent_and_points(self):
        self.assertEqual(kinds("Eval pass rate 91.3%"), [("pct", 91.3)])
        self.assertEqual(kinds("3 points short"), [("pct", 3.0)])
        self.assertEqual(kinds("12 percent"), [("pct", 12.0)])

    def test_counts_and_commas(self):
        self.assertEqual(kinds("9 of 11 commitments"), [("num", 9.0), ("num", 11.0)])
        self.assertEqual(kinds("1,049 checks"), [("num", 1049.0)])
        self.assertEqual(kinds("23.1K loads"), [("num", 23_100.0)])

    def test_labels_are_not_figures(self):
        for text in ["[L08]", "[[L01]]", "Q3 FY26", "30 Sep 2026", "2026-09-30", "Sep 2026", "Sev-2 incidents", "in 2026", "H1"]:
            self.assertEqual(figures(text), [], text)

    def test_month_names_need_a_whole_word(self):
        # "decisions" starts with "Dec" but is not a month.
        self.assertEqual(kinds("4 decisions"), [("num", 4.0)])

    def test_spelled_counts(self):
        self.assertEqual(kinds("three bets"), [("num", 3.0)])
        self.assertEqual(figures("one decision"), [])
        self.assertEqual(kinds("forty engineers"), [("num", 40.0)])
        self.assertEqual(kinds("revenue doubled"), [("num", 2.0)])

    def test_matching_needs_same_kind_and_value(self):
        self.assertTrue(Figure("money", 41_200_000, "").matches(Figure("money", 41.2e6, "")))
        self.assertFalse(Figure("pct", 41.2, "").matches(Figure("money", 41.2, "")))
        self.assertFalse(Figure("pct", 91.3, "").matches(Figure("pct", 91.4, "")))
        # Different spellings of one figure match.
        allowed = figures("ARR $41.2M")
        self.assertEqual(unmatched("ARR was $41.2 million", allowed), [])
        self.assertEqual([f.text for f in unmatched("ARR was $41.3M", allowed)], ["$41.3M"])

    def test_structured_value(self):
        self.assertEqual(value_figures(91.3, "%")[0].kind, "pct")
        self.assertEqual(value_figures(612000, "$")[0].kind, "money")
        self.assertEqual(value_figures(None, None), [])
        self.assertEqual(value_figures(True, None), [])


if __name__ == "__main__":
    unittest.main()
