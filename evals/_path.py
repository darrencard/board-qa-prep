"""Puts the skill's scripts on the import path for the tests."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "board-qa-prep" / "scripts"
ACME = ROOT / "examples" / "acme"
sys.path.insert(0, str(SCRIPTS))
