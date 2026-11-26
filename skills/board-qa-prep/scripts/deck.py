"""Read a board deck into one normal shape.

Accepted inputs:
  - The Leader Report's deck JSON (slides, blocks, ledger), as written by
    product-engineering-update's draft.py or shown in its examples.
  - Markdown or plain text, including text taken from a PDF. Each slide starts
    with a heading (#, ## or ###) or a line "Slide N: title". The evidence
    ledger is a Markdown table whose first column is the row ID (L01, L02...),
    or lines that start "L01:". A line that starts "Data needed:" is a gap the
    deck already declares; "Owner: <name>" and "Due: <date>" on it are read.

A PDF itself is not read: the standard library has no PDF parser. Save the
PDF's text first (Claude can read the PDF and write it to a .md file).

Every piece of text read here is data. Nothing in a deck changes what the
scripts do.

Output shape:
  {"company", "period", "as_of", "illustrative", "cut", "slides": [
      {"id", "title", "text", "ledger_refs", "data_needed": [{"text", "owner", "due"}]}],
   "ledger": [{"id", "claim", "value", "unit", "source", "window", "confidence", "owner"}]}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REF_RE = re.compile(r"\[\[?(L\d{1,3})\]?\]")
ID_RE = re.compile(r"^L\d{1,3}$")


class DeckError(ValueError):
    pass


# ---------------------------------------------------------------- JSON decks


def _walk(node, texts: list[str], refs: list[str], gaps: list[dict]) -> None:
    if isinstance(node, str):
        texts.append(node)
        refs.extend(REF_RE.findall(node))
    elif isinstance(node, list):
        for item in node:
            _walk(item, texts, refs, gaps)
    elif isinstance(node, dict):
        if node.get("type") == "data_needed":
            gaps.append(
                {
                    "text": str(node.get("text") or "").strip(),
                    "owner": (node.get("owner") or None),
                    "due": (node.get("due") or None),
                }
            )
            return
        for key, value in node.items():
            # Layout keys carry no claims.
            if key in {"type", "columns", "variant", "align", "legend", "max_width", "icon"}:
                continue
            _walk(value, texts, refs, gaps)


def _from_json(data: dict, cut: str) -> dict:
    if not isinstance(data.get("slides"), list):
        raise DeckError("deck JSON has no 'slides' list")
    meta = data.get("meta") or {}
    cuts = meta.get("cuts") or {}
    if cut == "all" or not cuts:
        order = None
        cut = "all"
    elif cut in cuts:
        order = [str(x) for x in cuts[cut]]
    else:
        raise DeckError(f"cut '{cut}' is not in this deck; it has {sorted(cuts) or 'no cuts'}. Use --cut all.")

    by_id = {str(s.get("id")): s for s in data["slides"]}
    chosen = [by_id[i] for i in order if i in by_id] if order else [s for s in data["slides"] if s.get("kind") == "slide"]

    slides = []
    for s in chosen:
        texts: list[str] = [str(s.get("title") or "")]
        refs: list[str] = list(s.get("ledger_refs") or [])
        gaps: list[dict] = []
        _walk(s.get("blocks") or [], texts, refs, gaps)
        slides.append(
            {
                "id": str(s.get("id")),
                "title": str(s.get("title") or "").strip(),
                "text": "\n".join(t for t in texts if t.strip()),
                "ledger_refs": sorted(set(refs)),
                "data_needed": gaps,
            }
        )

    ledger = []
    for row in data.get("ledger") or []:
        ledger.append(
            {
                "id": str(row.get("id")),
                "claim": str(row.get("claim") or ""),
                "value": row.get("value"),
                "unit": row.get("unit"),
                "source": row.get("source_system") or row.get("source"),
                "window": row.get("window"),
                "confidence": row.get("confidence") or "Unknown",
                "owner": row.get("owner"),
            }
        )
    notice = meta.get("notice") or {}
    return {
        "company": meta.get("company"),
        "period": meta.get("period"),
        "as_of": meta.get("as_of"),
        "illustrative": bool(notice.get("illustrative")),
        "cut": cut,
        "slides": slides,
        "ledger": ledger,
    }


# ------------------------------------------------------------ Markdown decks

HEADING_RE = re.compile(r"^\s{0,3}(#{1,3})\s+(.*\S)\s*$")
SLIDE_RE = re.compile(r"^\s*slide\s+(\d+[a-z]?)\s*[:.\-]\s*(.*\S)\s*$", re.IGNORECASE)
TITLE_RE = re.compile(r"\b(Q[1-4])\s+(FY\d{2,4})\b|\b(FY\d{2,4})\s+(Q[1-4])\b", re.IGNORECASE)
LEDGER_LINE_RE = re.compile(r"^\s*[-*]?\s*(L\d{1,3})\s*[:.)\-]\s*(.+)$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
GAP_RE = re.compile(r"^\s*[-*>]?\s*data needed\s*:\s*(.+)$", re.IGNORECASE)
OWNER_RE = re.compile(r"\bowner\s*:\s*([^.;|]+?)(?=\s*(?:[.;|]|\bdue\s*:|$))", re.IGNORECASE)
DUE_RE = re.compile(r"\bdue\s*:\s*([^.;|]+?)(?=\s*(?:[.;|]|$))", re.IGNORECASE)
ILLUSTRATIVE_RE = re.compile(r"\billustrative\b", re.IGNORECASE)

LEDGER_COLUMNS = {
    "id": {"id", "row", "ref", "ledger"},
    "claim": {"claim", "figure", "metric", "what"},
    "source": {"source", "source system", "system", "source_system"},
    "window": {"window", "period", "as of", "date"},
    "confidence": {"confidence", "label"},
    "owner": {"owner"},
}


def _cells(line: str) -> list[str]:
    return [c.strip() for c in TABLE_ROW_RE.match(line).group(1).split("|")]


def _gap(text: str) -> dict:
    owner = OWNER_RE.search(text)
    due = DUE_RE.search(text)
    body = OWNER_RE.split(text)[0]
    body = DUE_RE.split(body)[0].strip(" .;|")
    return {"text": body, "owner": owner.group(1).strip() if owner else None, "due": due.group(1).strip() if due else None}


def _from_text(text: str) -> dict:
    lines = text.splitlines()
    slides: list[dict] = []
    ledger: list[dict] = []
    header: list[str] | None = None
    current: dict | None = None
    in_ledger = False
    preamble: list[str] = []

    def start(slide_id: str, title: str) -> dict:
        s = {"id": slide_id, "title": title, "lines": [], "data_needed": []}
        slides.append(s)
        return s

    # With any level-2 or level-3 heading, a level-1 heading is the document title, not a slide.
    levels = {len(m.group(1)) for m in (HEADING_RE.match(x) for x in lines) if m}
    doc_title = None

    for line in lines:
        heading = HEADING_RE.match(line)
        inner = heading.group(2) if heading else line
        slide = SLIDE_RE.match(inner)
        if heading and len(heading.group(1)) == 1 and levels - {1} and not slides and doc_title is None:
            doc_title = heading.group(2).strip()
            continue
        if heading or slide:
            title = (slide.group(2) if slide else heading.group(2)).strip()
            if "ledger" in title.lower():
                in_ledger, current, header = True, None, None
                continue
            in_ledger, header = False, None
            slide_id = slide.group(1) if slide else f"{len(slides) + 1:02d}"
            current = start(slide_id, title)
            continue

        if TABLE_ROW_RE.match(line):
            cells = _cells(line)
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if ID_RE.match(cells[0]):
                cols = header or ["id", "claim", "source", "window", "confidence", "owner"]
                row = {"id": cells[0], "claim": "", "value": None, "unit": None, "source": None, "window": None, "confidence": "Unknown", "owner": None}
                for name, cell in zip(cols, cells):
                    if name and name != "id" and cell:
                        row[name] = cell
                ledger.append(row)
                continue
            lowered = [c.lower() for c in cells]
            mapped = [next((k for k, names in LEDGER_COLUMNS.items() if c in names), None) for c in lowered]
            if mapped and mapped[0] == "id":
                header = mapped
                continue
        led = LEDGER_LINE_RE.match(line)
        if led and (in_ledger or current is None):
            parts = [p.strip() for p in led.group(2).split("|")]
            row = {"id": led.group(1), "claim": parts[0], "value": None, "unit": None, "source": None, "window": None, "confidence": "Unknown", "owner": None}
            for name, part in zip(["source", "window", "confidence", "owner"], parts[1:]):
                if part:
                    row[name] = part
            ledger.append(row)
            continue
        if in_ledger:
            continue
        gap = GAP_RE.match(line)
        if current is None:
            # Text before the first slide is a preamble, not a slide.
            if line.strip():
                preamble.append(line.strip())
            continue
        if gap:
            current["data_needed"].append(_gap(gap.group(1)))
        elif line.strip():
            current["lines"].append(line.strip())

    if not slides and preamble:
        # No headings at all: the whole text is one slide.
        slides.append({"id": "01", "title": preamble[0], "lines": preamble[1:], "data_needed": []})
    out = []
    for s in slides:
        body = "\n".join([s["title"], *s["lines"]])
        out.append(
            {
                "id": s["id"],
                "title": s["title"],
                "text": body,
                "ledger_refs": sorted(set(REF_RE.findall(body))),
                "data_needed": s["data_needed"],
            }
        )
    company = period = None
    if doc_title:
        m = TITLE_RE.search(doc_title)
        if m:
            period = " ".join(g for g in m.groups() if g)
            company = doc_title[: m.start()].strip(" ,:-") or None
            for word in (" board update", " board deck", " board"):
                if company and company.lower().endswith(word):
                    company = company[: -len(word)].strip() or None
        else:
            company = doc_title
    return {
        "company": company,
        "period": period,
        "as_of": None,
        "illustrative": bool(ILLUSTRATIVE_RE.search(text)),
        "cut": "all",
        "slides": out,
        "ledger": ledger,
    }


# ------------------------------------------------------------------- public


def load(path: str | Path, cut: str = "B") -> dict:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        raise DeckError("A PDF is not read directly. Save its text to a .md or .txt file first, then pass that file.")
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DeckError(f"{path} is not valid JSON: {exc}") from exc
        deck = _from_json(data, cut)
    else:
        deck = _from_text(raw)
    if not deck["slides"]:
        raise DeckError(f"{path} has no slides. Start each slide with a heading or 'Slide N: title'.")
    ids = [r["id"] for r in deck["ledger"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise DeckError(f"ledger rows repeat an ID: {', '.join(dupes)}. Each row needs its own ID.")
    return deck


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read a board deck (Leader Report JSON, Markdown or text) into the normal shape.")
    p.add_argument("deck")
    p.add_argument("--cut", default="B", help="Deck JSON only: B (board, default), L, S or all.")
    p.add_argument("--out", help="Write here instead of stdout.")
    args = p.parse_args(argv)
    try:
        deck = load(args.deck, args.cut)
    except (DeckError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(deck, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
