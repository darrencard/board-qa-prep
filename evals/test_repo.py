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
        self.assertIn('<span class="ill">Illustrative</span>', page)
        self.assertNotRegex(page, r"""(src|href)=["']https?://""")
        self.assertNotIn("<script", page)

    def test_green_only_for_status_and_once(self):
        page = (ACME / "board-qa-prep.html").read_text(encoding="utf-8")
        body = page.split("</style>", 1)[1]
        self.assertEqual(len(re.findall(r'class="st (landed|watch|stalled)"', body)), 1)
        self.assertNotIn("--landed", render_html.PAGE_CSS)
        # Brass marks a person's call only: an open question's owner and due date. Check chips are ink.
        self.assertEqual(set(re.findall(r"([.\w-]+)\{[^}]*--brass", render_html.PAGE_CSS)), {".own"})

    def test_selection_and_focus_print_in_ink_not_green(self):
        css = re.search(r"<style>(.*?)</style>", (ACME / "board-qa-prep.html").read_text(encoding="utf-8"), re.S).group(1)
        self.assertLess(css.index("::selection{background:var(--landed)"), css.index("::selection{background:var(--t1)"))
        self.assertLess(css.index("outline:2px solid var(--landed)"), css.index(":focus-visible{outline-color:var(--t1)}"))

    def test_a_leader_gets_the_point_in_thirty_seconds(self):
        page = (ACME / "board-qa-prep.html").read_text(encoding="utf-8")
        body = page.split("</style>", 1)[1]
        key = json.loads((ACME / "landing" / "quote-drafting.json").read_text(encoding="utf-8"))["board_qa"]
        self.assertIn(f'<p class="answer">{render_html.e(render_html.answer_line(key))}</p>', body)
        self.assertEqual(len(re.findall(r"<li><b>Q\d\d</b>", re.search(r'<ul class="sum">(.*?)</ul>', body).group(1))), 5)
        visible = re.sub(r"<details.*?</details>", "", body, flags=re.S)
        for qid in key["first"]:
            self.assertIn(f'<div id="{qid}">', visible)
        folded = "".join(re.findall(r"<details.*?</details>", body, flags=re.S))
        rest = [q["id"] for q in key["questions"] if q["id"] not in key["first"]]
        self.assertTrue(rest)
        for qid in rest:
            self.assertIn(f'<div id="{qid}">', folded)
        self.assertLess(len(re.sub(r"<[^>]+>", " ", visible).split()), 600)
        md = (ACME / "board-qa-prep.md").read_text(encoding="utf-8")
        self.assertIn(f"**{render_html.answer_line(key)}**", md.split("## Prepare these first")[0])
        self.assertIn("<details>", md)

    def test_the_readme_excerpt_is_real_output(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        block = readme.split("## Try it on Acme", 1)[1].split("```text", 1)[1].split("```", 1)[0]
        md = (ACME / "board-qa-prep.md").read_text(encoding="utf-8")
        for para in [p for p in block.split("\n\n") if p.strip()]:
            self.assertIn(para.strip(), md)


class Floor(unittest.TestCase):
    def test_every_entry_script_stops_on_an_old_python_with_a_plain_message(self):
        for path in (SCRIPTS / "board_qa.py", SCRIPTS / "check.py", ACME / "sample.py"):
            code = f"import runpy, sys; sys.version_info = (3, 9, 6); runpy.run_path({str(path)!r}, run_name='__main__')"
            done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30, check=False)  # noqa: S603
            self.assertEqual(done.returncode, 1, path.name)
            self.assertIn("board-qa-prep needs Python 3.11 or later; try python3.12", done.stderr, path.name)


class Versions(unittest.TestCase):
    def test_every_version_field_is_0_3_0(self):
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        skill = re.search(r'version: "([^"]+)"', (SKILL / "SKILL.md").read_text(encoding="utf-8")).group(1)
        log = re.search(r"^## (\S+), (\d{4}-\d{2}-\d{2})", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
        self.assertEqual({plugin, project, skill, board_qa.VERSION, log.group(1)}, {"0.3.0"})
        self.assertEqual(log.group(2), "2026-11-26")


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
