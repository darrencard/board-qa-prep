"""House rules for the repository: the sample reproduces, versions agree, pins hold, and the words follow the voice."""

import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from _path import ACME, ROOT, SCRIPTS

# isort: split
import board_qa
import landing_brief
import render_html
import svgkit

SKILL = SCRIPTS.parent
OUTPUTS = ("board-qa-prep.html", "board-qa-prep.md", "landing/quote-drafting.json")
TEXT = [
    p
    for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in {".md", ".py", ".json", ".toml", ".yml", ".html"} and not {".git", ".ruff_cache", "vendor"} & set(p.parts) and p.name != "landing_brief.py"
]
BANNED = re.compile(r"\b(AI-powered|unlock|supercharge|seamless|robust|get started|sign up|leverages?|leveraging)\b", re.I)
# CSS keeps its own spelling (color:, color-scheme); prose does not.
AMERICAN = re.compile(r"\b(behavior|organization|organize|prioritize|prioritization|licensed under)\b|\bcolor\b(?![-:])")


def sample_into(d: Path) -> int:
    import importlib.util

    spec = importlib.util.spec_from_file_location("acme_sample", ACME / "sample.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with contextlib.redirect_stdout(io.StringIO()):
        return mod.main(["--into", str(d)])


class Sample(unittest.TestCase):
    def test_the_readme_command_reproduces_the_committed_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sample_into(Path(tmp)), 0)
            for name in OUTPUTS:
                self.assertEqual((Path(tmp) / name).read_bytes(), (ACME / name).read_bytes(), f"{name} differs: run python3 examples/acme/sample.py and commit")

    def test_the_sample_starts_from_the_landing_loop_record(self):
        up = json.loads((ACME / "upstream" / "quote-drafting.json").read_text(encoding="utf-8"))
        self.assertEqual(up["brief"]["sha256"], hashlib.sha256((ACME / "briefs" / "quote-drafting.md").read_bytes()).hexdigest())
        self.assertEqual(up["brief"]["sha256"], "decbe39590cc57b3d47125722a8d43e445d33c8f2f525c00277b94b7937dc95f")
        out = json.loads((ACME / "landing" / "quote-drafting.json").read_text(encoding="utf-8"))
        self.assertEqual({k: v for k, v in out.items() if k != "board_qa"}, up)
        self.assertEqual(out["board_qa"]["as_of"], "2026-11-26")

    def test_the_page_is_self_contained_and_marked_illustrative(self):
        page = (ACME / "board-qa-prep.html").read_text(encoding="utf-8")
        self.assertIn('<span class="sk-ill">Illustrative</span>', page)
        self.assertIn(":root{--ill:#74A5DA}", page, "the Illustrative tag is blue")
        self.assertNotIn('class="ill"', page, "the template's grey tag")
        self.assertNotRegex(page, r"""(src|href)=["']https?://""")
        self.assertNotIn("<script", page)

    def test_green_only_for_status_and_once(self):
        page = (ACME / "board-qa-prep.html").read_text(encoding="utf-8")
        body = page.split("</style>", 1)[1]
        self.assertEqual(len(re.findall(r'class="st (landed|watch|stalled)"', body)), 1)
        self.assertNotIn("--landed", render_html.PAGE_CSS)
        # Brass marks a person's call only: an open question's owner and due date, in its row and in the next step.
        self.assertEqual(set(re.findall(r"([.\w> -]+)\{[^}]*--brass", render_html.PAGE_CSS)), {".own", ".next", ".next>b", ".next .who"})
        self.assertNotIn("brass", "".join(re.findall(r"\.wd[^{]*\{[^}]*\}", render_html.PAGE_CSS)), "check words are ink or muted")
        # In the rows, brass is only an open question's owner: one person call per open question.
        key = json.loads((ACME / "landing" / "quote-drafting.json").read_text(encoding="utf-8"))["board_qa"]
        opens = [q for q in key["questions"] if q["check"] == "open"]
        frame = svgkit.frames_in(body)[0]
        self.assertEqual(re.findall(r'<span class="sc-o">.*?</svg>([^<]+)</span>', frame), [q["owner"].removesuffix(", Quoting squad") for q in opens])

    def test_selection_and_focus_print_in_ink_not_green(self):
        css = re.search(r"<style>(.*?)</style>", (ACME / "board-qa-prep.html").read_text(encoding="utf-8"), re.S).group(1)
        self.assertLess(css.index("::selection{background:var(--landed)"), css.index("::selection{background:var(--t1)"))
        self.assertLess(css.index("outline:2px solid var(--landed)"), css.index(":focus-visible{outline-color:var(--t1)}"))

    def test_a_leader_gets_the_point_in_thirty_seconds(self):
        page = (ACME / "board-qa-prep.html").read_text(encoding="utf-8")
        body = page.split("</style>", 1)[1]
        key = json.loads((ACME / "landing" / "quote-drafting.json").read_text(encoding="utf-8"))["board_qa"]
        self.assertIn(f"<h1>{render_html.e(render_html.answer_line(key))}</h1>", body)
        self.assertEqual(render_html.answer_line(key), "The project file answers 13 of 15 likely board questions. Two need an owner's answer before the meeting.")
        visible = re.sub(r"<details.*?</details>", "", body, flags=re.S)
        for qid in key["first"]:
            self.assertIn(f'<div id="{qid}">', visible)
        # The five to prepare first show their point; each long answer folds behind them.
        five = body.split("The five to prepare first", 1)[1].split("<h3>", 1)[0]
        self.assertEqual(five.count("The full answer, with sources"), 4)  # Q15's answer is one sentence
        folded = "".join(re.findall(r"<details.*?</details>", body, flags=re.S))
        rest = [q["id"] for q in key["questions"] if q["id"] not in key["first"]]
        self.assertTrue(rest)
        for qid in rest:
            self.assertIn(f'<div id="{qid}">', folded)
        # 650: the scorecard rows print as text what the old tiles drew inside an SVG (ids, topics, owners), which this
        # count skipped; the page itself is no longer.
        self.assertLess(len(re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>|<svg.*?</svg>", "", visible, flags=re.S)).split()), 650)
        md = (ACME / "board-qa-prep.md").read_text(encoding="utf-8")
        self.assertTrue(md.startswith(f"# {render_html.answer_line(key)}\n"))
        self.assertIn("<details>", md.split("## The five to prepare first")[1])

    def test_the_readme_excerpt_is_real_output(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        block = readme.split("## Try it on Acme", 1)[1].split("```text", 1)[1].split("```", 1)[0]
        md = (ACME / "board-qa-prep.md").read_text(encoding="utf-8")
        for para in [p for p in block.split("\n\n") if p.strip()]:
            self.assertIn(para.strip(), md)


class Visual(unittest.TestCase):
    """The page in the Landing Loop's one visual family: svgkit pinned, the picture honest, the words plain."""

    @classmethod
    def setUpClass(cls):
        cls.page = (ACME / "board-qa-prep.html").read_text(encoding="utf-8")
        cls.md = (ACME / "board-qa-prep.md").read_text(encoding="utf-8")
        cls.key = json.loads((ACME / "landing" / "quote-drafting.json").read_text(encoding="utf-8"))["board_qa"]

    def test_svgkit_matches_its_landing_loop_pin(self):
        pin = json.loads((SKILL / "VENDORED.json").read_text(encoding="utf-8"))["landing-loop"]
        self.assertEqual(pin["commit"], "78784efd2ecd5282f6ec264e545ce2075e459be2")
        self.assertEqual(set(pin["files"]), {"scripts/vendor/svgkit.py"})
        for rel, info in pin["files"].items():
            digest = hashlib.sha256((SKILL / rel).read_bytes()).hexdigest()
            self.assertEqual(digest, info["sha256"], f"{rel} changed. Copy it again from landing-loop at the pinned commit and update VENDORED.json.")

    def test_the_visual_draws_only_figures_the_page_prints(self):
        self.assertEqual(svgkit.unprinted(self.page), [])
        frame = svgkit.frames_in(self.page)[0]
        n = {name: f["value"] for name, f in self.key["counts"].items()}
        # The share bar first: answered of all, its figure printed beside it.
        first = re.search(r'<div class="sc-r">.*?</span></div>', frame).group(0)
        self.assertIn(f'<span class="sc-l"><b>{n["answered"]} of {n["questions"]}</b></span>', first)
        self.assertIn('<svg class="sc-sh"', first)
        self.assertIn(f'width="{svgkit.num(n["answered"] / n["questions"] * 100)}%"', first)

    def test_green_and_red_only_beside_their_words(self):
        body = self.page.split("</style>", 1)[1]
        rest = re.sub(r'<span class="st (landed|stalled)">\1</span>', "", body)
        for word in ("landed", "stalled"):
            self.assertNotIn(f"var(--{word})", rest)
            self.assertNotIn(f"st {word}", rest)
        for row in re.findall(r'<div class="sc-r">.*?</div>', body):
            self.assertNotRegex(row, r'class="ac (landed|stalled)"')

    def test_each_visual_states_its_answer(self):
        labels = re.findall(r'role="img" aria-label="([^"]+)"', self.page)
        self.assertEqual(labels, ["The project file answers 13 of 15 likely board questions. Two need an owner&#x27;s answer before the meeting."])

    # The scorecard grammar (landing-loop tools/SCORECARD-ROLLOUT.md, svgkit 1.2.0)

    def css(self) -> str:
        return self.page.split("<style>", 1)[1].split("</style>", 1)[0]

    def test_no_text_inside_a_picture_and_no_picture_scales(self):
        self.assertEqual(svgkit.svgs_with_text(self.page), [], "text inside an SVG")
        self.assertEqual(svgkit.scaled_svgs_in(self.page), [], "a picture with a viewBox would scale")

    def test_labels_render_12px_and_names_14px(self):
        css = self.css()
        self.assertEqual(set(svgkit.font_sizes(css)), {"var(--sc-m)", "var(--sc-n)"})
        self.assertIn("--sc-m:calc(12px / var(--sc-z))", css)
        self.assertIn("--sc-n:calc(14px / var(--sc-z))", css)
        self.assertIn(".scg{--sc-z:1;", css, "a sample page has no zoom")

    def test_no_box_inside_the_frame_and_no_overlap(self):
        self.assertEqual(svgkit.boxes_in_frames(self.page, self.css()), [])
        self.assertNotIn('class="chip', self.page.split("For your engineers", 1)[0])
        self.assertNotIn("position:absolute", svgkit.SCORECARD_CSS)

    def test_no_legacy_svgkit_primitive_draws_on_the_page(self):
        import warnings

        self.assertEqual(svgkit.legacy_in(self.page), [])
        record = json.loads((ACME / "landing" / "quote-drafting.json").read_text(encoding="utf-8"))
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            render_html.page(record)

    def test_one_frame_the_share_row_then_open_then_answered(self):
        frames = svgkit.frames_in(self.page)
        self.assertEqual(len(frames), 1)
        names = re.findall(r'<span class="sc-n">([^<]+)</span>', frames[0])
        opens = [q["id"] for q in self.key["questions"] if q["check"] == "open"]
        done = [q["id"] for q in self.key["questions"] if q["check"] != "open"]
        self.assertEqual(len(names), 1 + len(self.key["questions"]))
        self.assertEqual([x.split(".", 1)[0] for x in names[1:]], opens + done)
        words = re.findall(r'<span class="sc-s">(.*?)</span></div>', frames[0])
        self.assertEqual(len(words), len(names))
        for w in words[1 : 1 + len(opens)]:
            self.assertIn('<span class="sc-w ink">open</span>', w)
            self.assertIn('class="sc-o"', w)
        for w in words[1 + len(opens) :]:
            self.assertEqual(w, '<span class="sc-w">answered</span>')

    def test_the_share_and_the_team_print_once_in_the_frame_head(self):
        frame = svgkit.frames_in(self.page)[0]
        head, body = frame.split('<div class="sc-b">', 1)
        self.assertIn("<span>Likely board questions</span><span>13 of 15 answered</span>", head)
        self.assertIn("</svg>Quoting squad</span>", head)
        self.assertNotIn("Quoting squad", body.split('<span class="sc-c">', 1)[0], "each row prints the role only")
        self.assertIn('<svg class="sc-sh"', body.split('<div class="sc-r">')[1], "the share bar stays the first row")
        self.assertEqual(render_html.team_of(["Lead, Quoting squad", "Head of Product, Quoting squad"]), "Quoting squad")
        self.assertEqual(render_html.team_of(["Lead, Quoting squad", "CFO"]), "")

    def test_the_answered_fold_into_details_and_the_open_stay_shown(self):
        frame = svgkit.frames_in(self.page)[0]
        shown, folded = frame.split('<details class="sc-d">', 1)
        opens = [q for q in self.key["questions"] if q["check"] == "open"]
        done = [q for q in self.key["questions"] if q["check"] != "open"]
        self.assertEqual(shown.count('<div class="sc-r">'), 1 + len(opens), "the share row and the open questions")
        self.assertIn('<summary class="sc-x">The 13 answered, with the steps each answer reads</summary>', folded)
        self.assertEqual(folded.split("</details>", 1)[0].count('<div class="sc-r">'), len(done))
        self.assertNotIn("answered</span></span></div>", shown)

    def test_a_row_without_a_picture_gives_its_name_the_picture_column_and_figures_print_in_one_case(self):
        css = self.css()
        self.assertIn("@container sc (min-width:800px){.scg .sc-r:has(>.sc-p:empty)>.sc-n{grid-column:1/3}.scg .sc-r:has(>.sc-p:empty)>.sc-p{display:none}}", css)
        self.assertIn(".scg .sc-l{text-transform:uppercase;letter-spacing:.06em}", css)
        self.assertIn(".scg .sc-d,.scg .sc-d::details-content{grid-column:1/-1;display:grid;grid-template-columns:subgrid}", css)

    def test_cited_check_words_are_the_contract_words(self):
        quality = next(q for q in self.key["questions"] if q["topic"] == "quality")
        self.assertIn("eval-kit's build check: not confirmed: too close to call.", quality["answer"])
        self.assertIn("NOT CONFIRMED: TOO CLOSE TO CALL", svgkit.page_text(self.page))
        self.assertEqual(board_qa.FLAG_WORDS["within-noise"], "inside normal ups and downs")

    def test_public_copy_uses_plain_words(self):
        public = svgkit.page_text(self.page.split("For your engineers", 1)[0]).lower()
        md = self.md.split("<summary>For your engineers</summary>", 1)[0].lower()
        for text in (public, md):
            for word in (
                " bet ",
                " bets ",
                " bar ",
                "held-out",
                "95% interval",
                "inside noise",
                "inside the noise",
                "vendor-a/xl",
                "waiver",
                "tokens per task",
                "rollback",
                ".json",
            ):
                self.assertNotIn(word, text)
            # The words a reader outside the loop does not know, as whole words.
            self.assertEqual(re.findall(r"\b(records?|bets?|the bar|prds?|arr|tokens?)\b", text), [])
            for word in ("project", "target", "likely range", "too close to call", "the large model"):
                self.assertIn(word, text)
        self.assertIn("<b>landing brief</b>, a one-page plan, sets what good looks like, by when and at what cost", self.page)

    def test_no_text_smaller_than_11px_at_any_width(self):
        css = " ".join(re.findall(r"<style>(.*?)</style>", self.page, re.S) + re.findall(r'style="([^"]*)"', self.page))
        sizes = [float(m) for m in re.findall(r"(?:font-size:\s*|font:[^;{}]*?)(\d+(?:\.\d+)?)px", css)]
        sizes += [float(m) for m in re.findall(r'font-size="(\d+(?:\.\d+)?)"', self.page)]
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), 11)
        # The vendored template is untouched on disk: the page raises its small sizes as it inlines them.
        self.assertIn("font:400 10px/16px", (SKILL / "assets" / "vendor" / "template.html").read_text(encoding="utf-8"))

    def test_header_prints_the_plain_name_and_the_fold_the_code_name(self):
        header = re.search(r'<header class="sk-hdr">.*?</header>', self.page, re.S).group(0)
        self.assertIn("<span>Board Q&amp;A prep</span>", header)
        self.assertNotIn("board-qa-prep", header)
        self.assertIn("<code>board-qa-prep</code>", self.page.split("For your engineers", 1)[1])
        self.assertIn("\nBoard Q&A prep v0.3.2.", self.md)

    def test_the_standard_gap_under_the_heading(self):
        self.assertIn("Nothing in the project file answers it", self.page)
        # The heading's gap is the family's: the same rules as did-it-land and eval-kit.
        self.assertIn(".solo h1{font-size:clamp(34px,4.6vw,60px);line-height:1;letter-spacing:-.04em;max-width:22ch;margin-bottom:20px}", self.page)
        self.assertIn(".solo .lede{margin-bottom:24px}", self.page)

    def test_the_page_follows_the_sample_anatomy(self):
        body = self.page.split('<main class="solo">', 1)[1]
        order = ['class="sk-hdr"', "<h1>", 'class="marks"', 'class="sc scg"', "What to do next", 'class="cols"', "For your engineers"]
        at = [body.index(x) for x in order]
        self.assertEqual(at, sorted(at))
        self.assertEqual(body.count('<div class="next">'), 1, "one next step leads the page")
        self.assertIn('<span class="o">Head of Product, Quoting squad</span><span class="d">before the board meeting</span>', body)
        self.assertIn("<span>Board Q&amp;A prep</span><span>As of 2026-11-26</span><span>v0.3.2</span>", body)
        self.assertNotIn("Book a call", body, "a sample is the skill's own output: no call to action")


class Floor(unittest.TestCase):
    def test_every_entry_script_stops_on_an_old_python_with_a_plain_message(self):
        for path in (SCRIPTS / "board_qa.py", SCRIPTS / "check.py", ACME / "sample.py"):
            code = f"import runpy, sys; sys.version_info = (3, 9, 6); runpy.run_path({str(path)!r}, run_name='__main__')"
            done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30, check=False)  # noqa: S603
            self.assertEqual(done.returncode, 1, path.name)
            self.assertIn("board-qa-prep needs Python 3.11 or later; try python3.12", done.stderr, path.name)


class Versions(unittest.TestCase):
    def test_every_version_field_is_0_3_2(self):
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        skill = re.search(r'version: "([^"]+)"', (SKILL / "SKILL.md").read_text(encoding="utf-8")).group(1)
        log = re.search(r"^## (\S+), (\d{4}-\d{2}-\d{2})", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
        self.assertEqual({plugin, project, skill, board_qa.VERSION, log.group(1)}, {"0.3.2"})
        self.assertEqual(log.group(2), "2026-11-27")


class Pins(unittest.TestCase):
    def test_vendored_files_match_their_pinned_hashes(self):
        manifest = json.loads((SKILL / "VENDORED.json").read_text(encoding="utf-8"))
        self.assertRegex(manifest["commit"], r"^[0-9a-f]{40}$")
        for rel, info in manifest["files"].items():
            self.assertEqual(hashlib.sha256((SKILL / rel).read_bytes()).hexdigest(), info["sha256"], rel)

    def test_brief_parser_is_the_one_the_loop_shares(self):
        digest = hashlib.sha256((SCRIPTS / "landing_brief.py").read_bytes()).hexdigest()
        self.assertTrue(digest.startswith("2d13573543c74ebe"), digest)

    def test_a_broken_brief_lists_every_problem(self):
        with self.assertRaises(landing_brief.BriefError) as e:
            landing_brief.parse("## Landing brief\n\n- **Metric:** Activation\n")
        self.assertIn("problem is missing", str(e.exception))


class Voice(unittest.TestCase):
    def test_no_em_or_en_dashes(self):
        for p in TEXT:
            text = p.read_text(encoding="utf-8")
            self.assertNotIn(chr(0x2014), text, p)
            self.assertNotIn(chr(0x2013), text, p)

    def test_no_banned_words(self):
        for p in TEXT:
            if p.name == "test_repo.py":
                continue
            m = BANNED.search(p.read_text(encoding="utf-8"))
            self.assertIsNone(m, f"{p}: {m and m.group(0)}")

    def test_british_spelling(self):
        for p in TEXT:
            if p.name == "test_repo.py" or "upstream" in p.parts or p.parent.name == "landing":
                continue
            text = p.read_text(encoding="utf-8")
            if p.suffix == ".html" or p.name == "render_html.py":
                text = re.sub(r"<style>.*?</style>|PAGE_CSS = \"\"\".*?\"\"\"", "", text, flags=re.S)  # CSS keeps its own spelling
            m = AMERICAN.search(text)
            self.assertIsNone(m, f"{p}: {m and m.group(0)}")


if __name__ == "__main__":
    unittest.main()
