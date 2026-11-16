#!/usr/bin/env python3
"""Check on the built deck that every request the presenter made is still met.

  python3 check_requests.py build/deck.pdf

Add one check per request, with the request in the message, when the request
is met; never delete one without the presenter's word. `source` is deck.tex;
`pages` is the text of each PDF page (pdftotext, poppler). Exits 1 and lists
every request that is no longer met.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def page_texts(pdf):
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return text.split("\f")[:-1]


def requests(source, pages):
    """(met, request) pairs. Replace the examples with the presenter's requests."""
    appendix = source.index(r"\appendix") if r"\appendix" in source else len(source)
    return [
        ("Questions?" in source[:appendix], "a questions frame closes the main talk"),
        (pages[-1].strip() == "", "the last page stays blank to draw on"),
    ]


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    broken = [request for met, request in requests((ROOT / "deck.tex").read_text(), page_texts(argv[1])) if not met]
    for request in broken:
        print(f"request no longer met: {request}")
    print(f"check_requests: {len(broken)} broken")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
