"""Shared paths for the tests. Every fixture figure is illustrative."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "board-qa-prep" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
HARBORLINE = FIXTURES / "harborline.deck.json"
ACME = FIXTURES / "acme-board.md"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
