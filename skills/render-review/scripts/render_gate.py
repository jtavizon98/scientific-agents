#!/usr/bin/env python3
"""Mechanical render checks that run before visual review.

Subcommands:

  lint-pdf PDF   Text, figure-canvas, LaTeX/Biber log and font checks on a final
                 PDF. Writes a JSON report; exits 1 if any finding is `fail`.
  packet PDF     Per-page PNGs, labelled contact sheets covering every page and
                 manifest.json with file and decoded-pixel hashes.
  diff OLD NEW   Decide per page whether an earlier visual verdict carries over.
  numbers PDF M  Find every value of an analyb.printed_values manifest in the
                 PDF text (pdftotext -layout) by analyb's matching rule.
  inventory PDF MAP
                 Compare page count, placed figures, headings and captions
                 with an analyb.plotbook_page_map; optionally check a plan.
  gate           Bind the inputs by hash, run lint-pdf, packet and, when given,
                 diff, numbers and inventory; apply session waivers and write
                  gate.json with detected failures, coverage and candidate pages.
   review-preflight
                  Validate bound evidence, explicit model and bounded page scope.

There is no combined score. Every finding carries `check`, `severity`
(`fail`, `flag` or `info`), `page` (1-based, or null for document- or
log-level findings), `bbox` ([x0, y0, x1, y1] in PDF points, origin at the
top-left of the page or figure canvas, y downwards, or null), `value` (the
measured quantity) and `message`. Figure findings have `page` null and add
`figure`, `figure_page` and `used_on_pages` (from pdfTeX's PTEX.FileName
records); their bbox is on the figure canvas. Log findings add `source`
(file:line).

Text geometry comes from MuPDF structured text (`mutool run`, accurate glyph
bounding boxes). Each page box is first enlarged in memory so glyphs lying
partly or wholly outside it are still extracted; text clipped away inside an
included figure's form box stays invisible, as it is on the page. Glyph boxes
are tight vertically and advance-width horizontally. Font sizes are the final
transformed sizes, so a figure scaled to half width reports half its font size.

Font thresholds are TeX points and are compared with a 0.05 pt tolerance, so
7 TeX pt (6.97 PDF pt) passes a 7 pt threshold. Text below `--min-font-pt`
(default 5) fails (`font-below-floor`); text below `--flag-font-pt` (default
7, the advisory tier) is flagged (`font-below-advisory`). Classified
sub/superscripts (see `scripts`: a run of 1-3 small glyphs right after larger
base text in the same line and text object) are reported once as
`font-below-floor`: fail below 0.7 x the floor (3.5 pt by default), flag
between that and the floor, and they skip the advisory tier.

Only painted text is checked: glyphs in invisible render mode or with zero
alpha are dropped (counted as `invisible`). Each structured-text glyph is matched to its painting occurrence by character
and paint order near its origin; a ligature's later characters, which
structured text places further along, are matched at the origin of the
preceding character's paint record (MuPDF paints them all there). Type 3
glyphs count as painted only when a nonzero-alpha path or image inside
their marked glyph-procedure scope precedes them at the glyph origin (or
within its em square). Unrelated page painting cannot establish visibility.
`unmatched` and
`ambiguous` (several candidates that disagree) glyphs are kept visible,
unclipped and never exempt as scripts, and pages with ambiguous matches get
an `extraction-ambiguous` info finding. Each glyph keeps the PDF
text object that painted it and the clip rectangle in force for it, e.g. an
included figure's form box. Overlaps are measured on the visible part of each
glyph; an intersection lying only in clipped-away ink is not a finding and is
counted in `counts.suppressed`, and a reported overlap involving a clipped
glyph carries `clipped: true`.

Figures are the included PDFs named by pdfTeX's PTEX.FileName records and,
with `--log`, the log's include records. Relative names resolve against the
log's directory, else the PDF's, the first that holds the file (latexmk's
`aux_dir` puts the log beside, not in, the directory TeX ran in). A named figure that is not on disk is a
`figure-unresolved` fail; `--figure` replaces the list and `--no-figure-check`
skips figure checks with one info finding. A `<stem>.figcheck.json` analyb
sidecar beside a figure is imported only if its schema, version and
`pdf_sha256` match the figure; otherwise `figure-sidecar-stale` fails. Its
boxes are kept in `figure_bbox` with their own `figure_bbox_units`; `bbox`
is null.

Density flags (advisory, never fail): each top-level form XObject placed on a
page (an included figure; its box is the form BBox under the placement CTM,
as MuPDF interprets the page) counts as one panel, and `panel-narrow` flags
one narrower than 4 cm. The content frame is the union, over all pages, of
the boxes of text blocks and placed XObjects (clipped to the page), i.e. the
area the document actually typesets into, header and footer included. A
document of fewer than 3 pages has too little content to infer that frame,
so each page's MediaBox inset by 12 mm is used instead (`density.frame` says
which). `page-underused` flags a page whose text-block and placement boxes
cover less than 50 % of the frame (union area on a 2 pt raster). `density` in the report lists every page's
fraction and panel sizes.

Blank bands (a configurable layout policy, fail by default): each
page is rasterized in grey at 36 dpi; a row is blank when every pixel across the density
frame's width is at least 250 of 255. The tallest run of blank rows inside the frame's
vertical extent, as a fraction of the page height, is `density.pages[].blank_band`. Above
`--max-blank-band` (default 0.25) it is a `page-blank-band` fail carrying the page's
`raster_sha256` at that resolution. The final page is measured but not checked. A
`--blank-exceptions` JSON list of `{raster_sha256, reason}` turns the matching page's
finding into `info` with `exception: reason`; an entry matching no such page is flagged
`blank-exception-unmatched`, and a malformed one fails `blank-exceptions-invalid`. Because
the hash covers the whole raster, an exception lapses when that page changes.

Slides profile (`--profile slides`, for Beamer decks and posters): blank-band
and density checks do not run, since whitespace on a slide is deliberate.
Beamer labels every overlay of a frame with the frame's page label and moves
text that a later overlay reveals far off the page, so pages are grouped into
frames by their PDF page labels; on every page but a frame's last, glyphs lying
wholly outside the page are hidden overlay text, skipped and counted in
`counts.suppressed.overlay-hidden`. Text crossing an edge still fails on every
page, and the last page of each frame is checked in full. A PDF without a flat
`/PageLabels` number tree, or a label range with a numbering style, makes every
page its own frame. Font findings for text inside a placed form XObject (an
included figure, as in the density checks) are flags (`in_figure` names it): a reused plot keeps its own sizes, and
the deck owner decides whether to re-render it. Text set on the slide itself
keeps the fail floor.

Gate: every input (PDF, log, Biber log, values manifest, page map, plan,
previous manifest, reviewed list, waivers.json, STATE.md) is hashed before
any check reads it, and each figure, sidecar and registered value-source
file just before it is read. `gate.json` binds those captured hashes. After all checks every bound file is
hashed again, and each step's view of the PDF is compared with the binding;
any difference is an `input-changed` fail. `blocked` is true when any `fail`
finding is not covered by a waiver; it is a gate state, not a score.

Every finding carries `fingerprint`, a hash of its check, page, figure, bbox
(rounded to 0.1 pt), value and message. A waiver in `<session>/waivers.json`
is `{id, check, fingerprint, pdf_sha256 | figure_sha256, reason,
approved_by}` and covers exactly one `fail` finding with that check and
fingerprint in that exact version. Findings carrying `figure` require
`figure_sha256`; other findings require `pdf_sha256`; one matching no finding
or several is listed as unmatched. It applies only when the session's
STATE.md has the line `waiver <id>: <reason> (approved by <identity>,
<YYYY-MM-DD>)` with the same id, reason and identity as `approved_by` and
the explicit `gate --approver` argument. This records approval evidence, not
authentication. `review_pages` is diff's review list, or every page without a
previous manifest. The gate refuses an existing output directory and exits
1 when blocked.

Numbers: the manifest must be analyb.printed_values version 4 with the same
`match_rule` text as MATCH_RULE here (a copy; analyb is not imported), else
`values-invalid`. Each source's file (a relative path is taken from the
manifest's directory) must exist with the recorded sha256, else
`source-stale`. Record pages must be positive integers or null, and non-null
source references must be registered. Malformed records are `values-invalid`.
A value whose `text` (with `context` on the same line, and on
`page` when given) matches no line is `value-missing` (fail); one matching
several lines is `value-ambiguous` (flag).

Inventory: the map must be analyb.plotbook_page_map version 1 with pages
numbered 1..page_count exactly once in order and consecutive two-column
row/column slots, else `pagemap-invalid`. `page-count` fails when the PDF's
page count differs. On
each mapped page the pdfTeX-included figures (PTEX.FileName forms, in content
order, resolved from the map's directory) must equal the map's slots:
`figure-missing`, `figure-extra`, `figure-misordered` fail. Actual row/column
positions must agree (`figure-misplaced`). The section heading and each
caption must match the exact text in their intended regions (MuPDF glyphs,
whitespace collapsed, line-end hyphens tolerated), excluding figure text. Each
caption is tied to its own figure; `heading-missing` / `caption-missing` fail.
The plan is a JSON list of
`{"figure": path relative to the map | "key": observable, "group": optional}`;
a key matches a slot whose figure file stem contains the key's letter/digit
tokens contiguously (`met` matches `J1_met_native` but not `mtlepmet`). An
item with no slot is `coverage-missing` (fail); a group whose items sit on
more than one page is `group-split` (flag).

Carry-over rule for `diff` (revised 2026-10-06): refuse when either
manifest is inconsistent (page_count, pages numbered 1..N in order, every PNG
present with the recorded decoded-pixel hash) or the two have different DPI.
A page carries its earlier verdict (`carry`) when its raster hash equals any
old page's and that hash appears in the reviewed list, including moved pages.
A page whose raster is new is `changed` and makes pages N-1
and N+1 `neighbour` reviews; an identical raster without a recorded review is
`unreviewed` and does not propagate. Contact sheets are always regenerated
for the whole book; the request selects useful sheets and page representatives.
Check sequence, numbering and routes separately. No footer pixels are masked.

The reviewed list (`--reviewed`) is a JSON array of objects:

  [{"raster_sha256": "<64 hex>", "verdict_ref": "<review record and finding>"}]

`raster_sha256` is the manifest's decoded-pixel hash (SHA-256 of
"<mode>:<width>x<height>:" followed by the raw pixel bytes), so PNG metadata
or compression differences do not affect it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

FLOOR_TOLERANCE = 0.05   # pt; thresholds are TeX pt, 7 TeX pt is 6.97 PDF pt
SCRIPT_FLOOR_FACTOR = 0.7  # sub/superscripts fail below this fraction of the floor
EDGE_TOLERANCE = 0.25    # pt a glyph box may cross a page or canvas edge
OVERLAP_MIN_PT = 0.5     # both sides of a glyph intersection must exceed this
OVERLAP_FRACTION = 0.25  # of the smaller glyph box
MAX_PRINT_LINE = 79      # TeX wraps log lines at this width
MARGIN = 2000            # pt added around each page box during extraction
PANEL_MIN_CM = 4.0       # narrower included figures are flagged (panel-narrow)
PAGE_USED_MIN = 0.5      # pages using less of the content frame are flagged (page-underused)
DENSITY_CELL = 2.0       # pt; raster cell for union areas
FRAME_INSET_PT = 12 / 25.4 * 72  # fallback density frame: the page inset by 12 mm
BLANK_BAND_MAX = 0.25    # of the page height; a taller blank band in the frame fails (page-blank-band)
BLANK_DPI = 36           # raster resolution of the blank-band check
BLANK_LEVEL = 250        # 8-bit grey at or above which a pixel counts as blank

CHARS_JS = r"""
var M = %d;
var doc = Document.openDocument(scriptArgs[0]);
// Mark the procedure scope in this in-memory extraction copy. The oversized clip
// paints nothing and leaves the glyph canvas intact; mode-3 text never enters it.
// Resources are traversed because fonts can live inside included forms.
var visited = {};
function markProcedures(res) {
  if (!res || !res.isDictionary()) return;
  var resourceKey = "resources:" + String(res);
  if (visited[resourceKey]) return;
  visited[resourceKey] = true;
  var fonts = res.get("Font"), objects = res.get("XObject");
  if (fonts && fonts.isDictionary()) fonts.forEach(function (font) {
    if (String(font.get("Subtype")) != "/Type3") return;
    var procs = font.get("CharProcs");
    if (procs && procs.isDictionary()) procs.forEach(function (proc) {
      var key = String(proc);
      if (!proc.isStream() || visited[key]) return;
      visited[key] = true;
      proc.writeStream("q -1000001 -1000000 2000001 2000000 re W n\n" + proc.readStream().asString() + "\nQ");
    });
    markProcedures(font.get("Resources"));
  });
  if (objects && objects.isDictionary()) objects.forEach(function (obj) {
    var key = "form:" + String(obj);
    if (visited[key]) return;
    visited[key] = true;
    markProcedures(obj.get("Resources"));
  });
}
for (var pi = 0; pi < doc.countPages(); pi++) markProcedures(doc.loadPage(pi).getObject().getInheritable("Resources"));
function box(o, key) {
  var a = o.getInheritable(key);
  if (!a || !a.isArray()) return null;
  var r = [a.get(0).asNumber(), a.get(1).asNumber(), a.get(2).asNumber(), a.get(3).asNumber()];
  return [Math.min(r[0], r[2]), Math.min(r[1], r[3]), Math.max(r[0], r[2]), Math.max(r[1], r[3])];
}
function f(v) { return v.toFixed(3); }
function nums(a) { var r = []; for (var k = 0; k < a.length; k++) r.push(a.get(k).asNumber()); return r; }
// Placements ("A" records) come from MuPDF's own interpretation of the page: every form
// XObject is clipped to its BBox when drawn, so a separate copy of the document tags each
// top-level form's BBox (x1 + a unique step) and the device recognises the tagged clip.
var tagged = Document.openDocument(scriptArgs[0]);
function placements(i) {
  var page = tagged.loadPage(i), res = page.getObject().getInheritable("Resources");
  var xo = res ? res.get("XObject") : null, forms = [];
  if (xo && xo.isDictionary()) xo.forEach(function (v, k) {
    if (!v.isStream() || String(v.get("Subtype")) != "/Form" || !v.get("BBox").isArray()) return;
    var bb = nums(v.get("BBox")), name = v.get("PTEX.FileName"), step = 0.001 * (forms.length + 1);
    forms.push({bbox: bb, step: step, ptex: name && name.isString(), name: name && name.isString() ? name.asString() : "/" + k});
    v.put("BBox", [bb[0], bb[1], bb[2] + step, bb[3]]);
  });
  function box(m, r) {
    var xs = [], ys = [];
    [[r[0], r[1]], [r[2], r[1]], [r[0], r[3]], [r[2], r[3]]].forEach(function (p) {
      xs.push(p[0] * m[0] + p[1] * m[2] + m[4]); ys.push(p[0] * m[1] + p[1] * m[3] + m[5]);
    });
    return [Math.min.apply(null, xs), Math.min.apply(null, ys), Math.max.apply(null, xs), Math.max.apply(null, ys)];
  }
  page = tagged.loadPage(i);
  page.run(new Device({
    clipPath: function (path, evenOdd, ctm) {
      var b = path.getBounds(null, Matrix.identity);
      for (var k = 0; k < forms.length; k++) {
        var bb = forms[k].bbox;
        if (Math.abs(b[0] - Math.min(bb[0], bb[2])) < 1e-3 && Math.abs(b[1] - Math.min(bb[1], bb[3])) < 1e-3
            && Math.abs(b[3] - Math.max(bb[1], bb[3])) < 1e-3
            && Math.abs(b[2] - Math.max(bb[0], bb[2]) - forms[k].step) < 4e-4) {
          print("A form " + (forms[k].ptex ? 1 : 0) + " " + box(ctm, bb).map(f).join(" ") + " " + JSON.stringify(forms[k].name));
          return;
        }
      }
    },
    fillImage: function (image, ctm) {
      print("A image 0 " + box(ctm, [0, 0, 1, 1]).map(f).join(" ") + " \"image\"");
    }
  }), Matrix.identity);
}
for (var i = 0; i < doc.countPages(); i++) {
  var page = doc.loadPage(i);
  var b = page.getBounds();
  var obj = page.getObject();
  var res = obj.getInheritable("Resources");
  var xo = res ? res.get("XObject") : null;
  if (xo && xo.isDictionary()) xo.forEach(function (v) {
    var name = v.get("PTEX.FileName");
    if (name && name.isString()) print("X " + JSON.stringify(name.asString()));
  });
  placements(i);
  var r = box(obj, "CropBox") || box(obj, "MediaBox");
  var big = [r[0] - M, r[1] - M, r[2] + M, r[3] + M];
  obj.put("MediaBox", big);
  obj.put("CropBox", big);
  page = doc.loadPage(i);
  var b2 = page.getBounds();
  var o = ((b2[2] - b2[0]) - (b[2] - b[0])) / 2;  // the margin in device units (scaled by /UserUnit)
  print("P " + f(b[2] - b[0]) + " " + f(b[3] - b[1]));
  // Painted glyphs: text object, visibility and the clip rectangle in force.
  var stack = [], procedures = [], id = 0;
  function push(q) { stack.push(q); }
  function clip() {
    var c = null;
    for (var k = 0; k < stack.length; k++) if (stack[k]) c = c ? [Math.max(c[0], stack[k][0]), Math.max(c[1], stack[k][1]),
      Math.min(c[2], stack[k][2]), Math.min(c[3], stack[k][3])] : stack[k];
    return c ? " " + [c[0] - o, c[1] - o, c[2] - o, c[3] - o].map(f).join(" ") : "";
  }
  // Visibility: 0 invisible, 1 direct text callback without procedure painting,
  // 2 direct text callback with procedure painting, 3 ignored text with procedure painting.
  // All Type 3 callback routes require procedure painting (confirmed with pdffonts):
  // MuPDF usually reports painted procedures as ignored text, but reports blank ones
  // through fillText/strokeText even though they paint nothing.
  // Path procedures are drawn with their origin at the glyph origin; image glyphs (bitmap
  // fonts) are matched by an image box lying within the glyph's em square.
  var paints = [];
  function paint(ctmAt, alphaAt, image) { return function () {
    var m = arguments[ctmAt];
    if (arguments[alphaAt] === 0 || !procedures.some(function (p) { return p; })) return;
    var xs = [m[4], m[0] + m[4], m[2] + m[4], m[0] + m[2] + m[4]];
    var ys = [m[5], m[1] + m[5], m[3] + m[5], m[1] + m[3] + m[5]];
    paints.push({x: m[4], y: m[5], box: image ? [Math.min.apply(null, xs), Math.min.apply(null, ys),
      Math.max.apply(null, xs), Math.max.apply(null, ys)] : null});
  }; }
  function procedureAt(x, y, em) {
    for (var k = 0; k < paints.length; k++) {
      var p = paints[k], b = p.box;
      if (b ? b[0] >= x - 0.5 * em && b[2] <= x + 2 * em && b[1] >= y - 1.5 * em && b[3] <= y + 0.5 * em
            : Math.abs(p.x - x) < 0.1 && Math.abs(p.y - y) < 0.1) return true;
    }
    return false;
  }
  function show(kind) { return function (text, a, b, c, d, e) {
    var ctm = kind == "stroke" ? b : a, alpha = kind == "stroke" ? e : d;
    var tail = clip();
    id++;
    text.walk({ showGlyph: function (font, trm, glyph, unicode) {
      var x = trm[4] * ctm[0] + trm[5] * ctm[2] + ctm[4], y = trm[4] * ctm[1] + trm[5] * ctm[3] + ctm[5];
      var em = Math.sqrt(Math.abs((trm[0] * trm[3] - trm[1] * trm[2]) * (ctm[0] * ctm[3] - ctm[1] * ctm[2])));
      var painted = procedureAt(x, y, em);
      var vis = kind == "ignore" ? (painted ? 3 : 0) : (alpha !== 0 ? (painted ? 2 : 1) : 0);
      print("G " + id + " " + f(x - o) + " " + f(y - o) + " " + unicode + " " + JSON.stringify(font.getName()) + " " + vis + tail);
    }});
    paints = [];
  }; }
  page.run(new Device({
    clipPath: function (p, e, ctm) {
      var bb = p.getBounds(null, Matrix.identity);
      var marker = bb[0] == -1000001 && bb[1] == -1000000 && bb[2] == 1000000 && bb[3] == 1000000;
      procedures.push(marker); push(marker ? null : p.getBounds(null, ctm));
    },
    clipStrokePath: function (p, s, ctm) { procedures.push(false); push(p.getBounds(s, ctm)); },
    clipText: function () { procedures.push(false); push(null); },
    clipStrokeText: function () { procedures.push(false); push(null); },
    clipImageMask: function () { procedures.push(false); push(null); },
    beginMask: function () { procedures.push(false); push(null); },
    popClip: function () { stack.pop(); procedures.pop(); },
    fillPath: paint(2, 5, false), strokePath: paint(2, 5, false),
    fillImage: paint(1, 2, true), fillImageMask: paint(1, 4, true),
    fillText: show("fill"), strokeText: show("stroke"), ignoreText: show("ignore")
  }), Matrix.identity);
  page.toStructuredText("accurate-bboxes").walk({
    beginTextBlock: function () { print("B"); },
    beginLine: function (bbox, wmode, dir) { print("L " + f(dir[0]) + " " + f(dir[1])); },
    onChar: function (c, p, font, size, q) {
      var v = [p[0], p[1], q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]];
      for (var k = 0; k < v.length; k++) v[k] = f(v[k] - o);
      print("C " + f(size) + " " + v.join(" ") + " " + JSON.stringify(c));
    }
  });
}
""" % MARGIN


# Small utilities

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def raster_sha256(path: Path) -> str:
    from PIL import Image
    with Image.open(path) as image:
        image.load()
        head = f"{image.mode}:{image.width}x{image.height}:".encode()
        return hashlib.sha256(head + image.tobytes()).hexdigest()


def tool_version(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    lines = (result.stdout + result.stderr).strip().splitlines()
    return lines[0] if lines else "unknown"


def finding(check, severity, message, page=None, bbox=None, value=None, **extra):
    item = {"check": check, "severity": severity, "page": page,
            "bbox": None if bbox is None else [round(v, 2) for v in bbox],
            "value": value, "message": message}
    item.update(extra)
    return fingerprinted(item)


def fingerprinted(item):
    """Add `fingerprint`: a hash of check, page, figure, bbox (0.1 pt), value and message."""
    bbox = None if item.get("bbox") is None else [round(v, 1) for v in item["bbox"]]
    basis = [item["check"], item.get("page"), item.get("figure"), bbox, item.get("value"),
             hashlib.sha256(str(item["message"]).encode()).hexdigest()]
    item["fingerprint"] = hashlib.sha256(json.dumps(basis, default=str).encode()).hexdigest()[:16]
    return item


def union(boxes):
    boxes = list(boxes)
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def snippet(text, limit=60):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 3] + "..."


# Glyph extraction

class Glyph:
    """One extracted character. `run` is the PDF text object that painted it
    (None if unknown); `vbox` is its box after the clip in force for it."""
    __slots__ = ("line", "size", "origin", "quad", "bbox", "dir", "text", "run", "vbox", "block")

    def __init__(self, line, size, origin, quad, direction, text, run=None, clip=None):
        self.line, self.size, self.origin, self.quad = line, size, origin, quad
        self.dir, self.text, self.run, self.block = direction, text, run, None
        xs, ys = [p[0] for p in quad], [p[1] for p in quad]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))
        self.vbox = self.bbox if clip is None else (
            max(self.bbox[0], clip[0]), max(self.bbox[1], clip[1]),
            min(self.bbox[2], clip[2]), min(self.bbox[3], clip[3]))

    @property
    def clipped(self):
        return any(abs(a - b) > EDGE_TOLERANCE for a, b in zip(self.bbox, self.vbox))

    @property
    def visible(self):
        return self.vbox[2] > self.vbox[0] and self.vbox[3] > self.vbox[1] or self.bbox == self.vbox

    def frame(self, direction):
        """Glyph rectangle in the (along, across) frame of a text direction."""
        dx, dy = direction
        along = [x * dx + y * dy for x, y in self.quad]
        across = [y * dx - x * dy for x, y in self.quad]
        return min(along), min(across), max(along), max(across)


MUPDF_MIN = (1, 26)


def require_mupdf():
    """Stop with an install hint when mutool predates the JavaScript Device API."""
    found = tool_version(["mutool", "-v"])
    match = re.search(r"(\d+)\.(\d+)", found)
    if not match or tuple(map(int, match.groups())) < MUPDF_MIN:
        raise SystemExit(f"render_gate needs MuPDF {'.'.join(map(str, MUPDF_MIN))} or newer, found: {found}. "
                         "Install it from your package manager or conda-forge (package mupdf).")


def extract(pdf: Path):
    """Return (pages, embedded figure names per page) from MuPDF structured text."""
    require_mupdf()
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as script:
        script.write(CHARS_JS)
    try:
        result = subprocess.run(["mutool", "run", script.name, str(pdf)],
                                capture_output=True, text=True)
    finally:
        os.unlink(script.name)
    if result.returncode:
        raise RuntimeError(f"mutool run failed for {pdf}: {result.stderr.strip()}")
    type3 = {name for name, kind, _ in pdf_fonts(pdf) if kind == "Type 3"}
    pages, figures, pending, painted, placed = [], [], [], {}, []
    line_id, block_id, direction, sequence, previous = -1, -1, (1.0, 0.0), 0, None
    for raw in result.stdout.splitlines():
        kind, _, rest = raw.partition(" ")
        if kind == "X":
            pending.append(json.loads(rest))
        elif kind == "P":
            width, height = map(float, rest.split())
            pages.append({"width": width, "height": height, "glyphs": [], "invisible": 0, "unmatched": 0,
                          "ambiguous": 0, "placements": placed})
            figures.append(pending)
            pending, painted, placed = [], {}, []
        elif kind == "A":
            kind_, ptex, x0, y0, x1, y1, name = rest.split(" ", 6)
            placed.append({"kind": kind_, "ptex": ptex == "1", "bbox": [float(x0), float(y0), float(x1), float(y1)],
                           "name": json.loads(name)})
        elif kind == "B":
            block_id += 1
        elif kind == "G":
            head, font, tail = re.match(r'(\S+ \S+ \S+ \S+) ("(?:[^"\\]|\\.)*") (.*)', rest).groups()
            run, x, y, code = head.split()
            tail = tail.split()
            is_type3 = json.loads(font) in type3
            visible = tail[0] in ("2", "3") if is_type3 else tail[0] in ("1", "2")
            # A blank Type 3 procedure can emit both fillText and strokeText for one
            # glyph. Their distinct callback IDs must not make known-invisible text
            # ambiguous; there is no painted text object to retain for these records.
            run = None if is_type3 and not visible else int(run)
            clip = tuple(map(float, tail[1:5])) if len(tail) > 1 else None
            x, y = float(x), float(y)
            sequence += 1
            painted.setdefault((chr(int(code)), int(x), int(y)), []).append(
                {"x": x, "y": y, "run": run, "visible": visible, "clip": clip, "used": False,
                 "seq": sequence})
        elif kind == "L":
            line_id, previous = line_id + 1, None
            direction = tuple(map(float, rest.split()))
        elif kind == "C":
            fields = rest.split(" ", 11)
            values = list(map(float, fields[:11]))
            text = json.loads(fields[11])
            quad = [(values[k], values[k + 1]) for k in range(3, 11, 2)]
            page = pages[-1]
            status, paint = match_paint(painted, text, values[1], values[2]) if text.strip() else ("blank", None)
            if status == "unmatched" and previous:
                # Ligature parts: structured text advances their origins, but MuPDF paints
                # every character of the ligature at the ligature glyph's origin.
                status, paint = match_paint(painted, text, previous["x"], previous["y"])
            previous = paint or previous
            if status in ("unmatched", "ambiguous"):
                page[status] += 1
            run, visible, clip = (paint["run"], paint["visible"], paint["clip"]) if paint else (None, True, None)
            glyph = Glyph(line_id, values[0], (values[1], values[2]), quad, direction, text, run, clip)
            glyph.block = block_id
            if visible and glyph.visible:
                page["glyphs"].append(glyph)
            elif text.strip():
                page["invisible"] += 1
    return pages, figures


def match_paint(painted, text, x, y, reach=0.15):
    """Match a structured-text glyph to its painting occurrence: same character
    within `reach` pt of the origin, the earliest unused one in paint order.
    Several unused candidates that disagree on visibility, clip or text object
    are ambiguous: the glyph is then kept visible, unclipped and unexempt."""
    candidates = sorted(
        (item for i in (-1, 0, 1) for j in (-1, 0, 1)
         for item in painted.get((text, int(x) + i, int(y) + j), ())
         if not item["used"] and abs(item["x"] - x) <= reach and abs(item["y"] - y) <= reach),
        key=lambda item: item["seq"])
    if not candidates:
        return "unmatched", None
    candidates[0]["used"] = True
    if len({(c["run"], c["visible"], c["clip"]) for c in candidates}) > 1:
        return "ambiguous", None
    return "matched", candidates[0]


def lines_text(glyphs):
    text = defaultdict(str)
    for glyph in glyphs:
        text[glyph.line] += glyph.text
    return text


def grid(glyphs, cell=12.0):
    cells = defaultdict(list)
    for index, glyph in enumerate(glyphs):
        x0, y0, x1, y1 = glyph.bbox
        for i in range(int(x0 // cell), int(x1 // cell) + 1):
            for j in range(int(y0 // cell), int(y1 // cell) + 1):
                cells[i, j].append(index)
    return cells


def neighbours(cells, glyph, reach, cell=12.0):
    x0, y0, x1, y1 = glyph.bbox
    found = set()
    for i in range(int((x0 - reach) // cell), int((x1 + reach) // cell) + 1):
        for j in range(int((y0 - reach) // cell), int((y1 + reach) // cell) + 1):
            found.update(cells.get((i, j), ()))
    return found


# Text checks on one page

def scripts(glyphs):
    """Glyphs classified as sub/superscripts.

    Exponents and indices are short, so only a run of 1-3 consecutive small
    glyphs that immediately follows larger base text in the same structured-
    text line qualifies. The base glyph must be painted by the same PDF text
    object and be at least 1.2x larger; the run's first glyph must sit right
    beside it, overlap it vertically and have its baseline offset by at least
    0.12 em. Every glyph of the run must have the base's known text object;
    unmatched or ambiguous glyphs (no known text object) keep ordinary-text
    checks. Longer runs, or anything uncertain, stay ordinary text."""
    def offset(a, b):  # baseline of a relative to b, positive = below
        dx, dy = b.dir
        return (a.origin[1] - b.origin[1]) * dx - (a.origin[0] - b.origin[0]) * dy

    def beside(glyph, base):
        fa, fb = glyph.frame(base.dir), base.frame(base.dir)
        gap = max(fa[0] - fb[2], fb[0] - fa[2])
        return (glyph.run is not None and base.run == glyph.run
                and glyph.dir[0] * base.dir[0] + glyph.dir[1] * base.dir[1] > 0.99
                and abs(offset(glyph, base)) >= 0.12 * base.size
                and min(fa[3], fb[3]) - max(fa[1], fb[1]) > 0
                and -0.3 * glyph.size <= gap <= 0.35 * base.size)

    lines = defaultdict(list)
    for glyph in glyphs:  # structured-text order within each line
        lines[glyph.line].append(glyph)
    found = set()
    for sequence in lines.values():
        k = 1
        while k < len(sequence):
            base, first = sequence[k - 1], sequence[k]
            if not (base.text.strip() and first.text.strip() and base.size >= 1.2 * first.size):
                k += 1
                continue
            end = k
            while (end < len(sequence) and sequence[end].text.strip()
                   and abs(sequence[end].size - first.size) <= 0.02 * first.size):
                end += 1
            run = sequence[k:end]
            if (end - k <= 3 and beside(first, base)
                    and all(glyph.run is not None and glyph.run == base.run for glyph in run)):
                found.update(map(id, run))
            k = end
    return found


def spans(glyphs, indices):
    """Group glyph indices into runs sharing a line and a size."""
    groups = defaultdict(list)
    for index in sorted(indices):
        glyph = glyphs[index]
        groups[glyph.line, round(glyph.size, 2)].append(glyph)
    return groups


def check_fonts(number, glyphs, floor, advisory=None):
    findings = []
    visible = [g for g in glyphs if g.text.strip()]
    if not visible:
        return findings, {"page": number, "min_base_pt": None, "snippet": ""}
    small = {i for i, g in enumerate(visible) if g.size < floor - FLOOR_TOLERANCE}
    classified = scripts(glyphs)
    script = {i for i, g in enumerate(visible) if id(g) in classified}
    texts = lines_text(glyphs)
    for (line, size), group in spans(visible, small - script).items():
        findings.append(finding(
            "font-below-floor", "fail",
            f"{size:.2f} pt text below the {floor:g} pt floor: {snippet(''.join(g.text for g in group))!r}"
            f" in {snippet(texts[line])!r}",
            number, union(g.bbox for g in group), size))
    if advisory is not None:
        soft = {i for i, g in enumerate(visible) if g.size < advisory - FLOOR_TOLERANCE} - small - script
        for (line, size), group in spans(visible, soft).items():
            findings.append(finding(
                "font-below-advisory", "flag",
                f"{size:.2f} pt text below the {advisory:g} pt advisory size: "
                f"{snippet(''.join(g.text for g in group))!r} in {snippet(texts[line])!r}",
                number, union(g.bbox for g in group), size))
    script_floor = SCRIPT_FLOOR_FACTOR * floor
    for (line, size), group in spans(visible, script & small).items():
        severity = "fail" if size < script_floor - FLOOR_TOLERANCE else "flag"
        findings.append(finding(
            "font-below-floor", severity,
            f"{size:.2f} pt sub/superscript below the {floor:g} pt floor (fails below {script_floor:g} pt): "
            f"{snippet(''.join(g.text for g in group))!r} in {snippet(texts[line])!r}",
            number, union(g.bbox for g in group), size))
    base = [g for i, g in enumerate(visible) if i not in script]
    least = min(base or visible, key=lambda g: g.size)
    summary = {"page": number, "min_base_pt": round(least.size, 2),
               "snippet": snippet(texts[least.line])}
    return findings, summary


def intersection(a, b):
    """Intersection rectangle of two boxes and its fraction of the smaller box, or None."""
    width = min(a[2], b[2]) - max(a[0], b[0])
    height = min(a[3], b[3]) - max(a[1], b[1])
    if width <= OVERLAP_MIN_PT or height <= OVERLAP_MIN_PT:
        return None
    fraction = width * height / min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    if fraction <= OVERLAP_FRACTION:
        return None
    return fraction, [max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])]


def check_overlap(number, glyphs):
    """text-overlap findings, and the number of glyph intersections that lie
    entirely in ink removed by the clip in force for one of the glyphs."""
    visible = [g for g in glyphs if g.text.strip()
               and g.bbox[2] - g.bbox[0] > 0 and g.bbox[3] - g.bbox[1] > 0]
    cells = grid(visible)
    texts = lines_text(glyphs)
    pairs, hidden = defaultdict(list), 0
    for index, glyph in enumerate(visible):
        for other in neighbours(cells, glyph, 0):
            peer = visible[other]
            if other <= index or peer.line == glyph.line:
                continue
            same = abs(glyph.dir[0] * peer.dir[0] + glyph.dir[1] * peer.dir[1]) > 0.999
            full = (intersection(glyph.frame(glyph.dir), peer.frame(glyph.dir)) if same
                    else intersection(glyph.bbox, peer.bbox))
            if full is None:
                continue
            clipped = glyph.clipped or peer.clipped
            hit = intersection(glyph.vbox, peer.vbox) if clipped else full
            if hit is None:
                hidden += 1
                continue
            box = intersection(glyph.vbox, peer.vbox) or full
            pairs[tuple(sorted((glyph.line, peer.line)))].append((hit[0], box[1], clipped))
    findings = []
    for (first, second), hits in pairs.items():
        findings.append(finding(
            "text-overlap", "fail",
            f"{snippet(texts[first])!r} overlaps {snippet(texts[second])!r} "
            f"({len(hits)} glyph intersections)",
            number, union(h[1] for h in hits), round(max(h[0] for h in hits), 3),
            clipped=any(h[2] for h in hits)))
    return findings, hidden


def outside(glyphs, width, height, tolerance):
    """Per text line, glyphs crossing the box edge and the largest overhang."""
    lines = defaultdict(list)
    for glyph in glyphs:
        if not glyph.text.strip():
            continue
        x0, y0, x1, y1 = glyph.vbox
        overhang = max(-x0, -y0, x1 - width, y1 - height)
        if overhang > tolerance:
            lines[glyph.line].append((overhang, glyph))
    return lines


def edges(bbox, width, height, tolerance):
    names = (("left", -bbox[0]), ("top", -bbox[1]), ("right", bbox[2] - width), ("bottom", bbox[3] - height))
    return "/".join(name for name, amount in names if amount > tolerance)


def check_outside(check, glyphs, width, height, page=None, **extra):
    findings = []
    texts = lines_text(glyphs)
    for line, hits in outside(glyphs, width, height, EDGE_TOLERANCE).items():
        box = union(g.vbox for _, g in hits)
        where = "page" if check == "text-off-page" else "figure canvas"
        findings.append(finding(
            check, "fail",
            f"{len(hits)} glyph(s) of {snippet(texts[line])!r} cross the "
            f"{edges(box, width, height, EDGE_TOLERANCE)} {where} edge "
            f"({width:.1f} x {height:.1f} pt)",
            page, box, round(max(h for h, _ in hits), 2), **extra))
    return findings


def frame_ends(pdf: Path, count):
    """1-based pages that end a frame: the last of each page-label range without a numbering style."""
    result = subprocess.run(["mutool", "show", str(pdf), "trailer/Root/PageLabels/Nums"],
                            capture_output=True, text=True)
    ranges = [(int(start), "/S" in body) for start, body in re.findall(r"(\d+)\s*<<(.*?)>>", result.stdout, re.S)]
    if result.returncode or not ranges or ranges[0][0] != 0:
        return set(range(1, count + 1))
    ends = set()
    for (start, styled), (stop, _) in zip(ranges, ranges[1:] + [(count, False)]):
        ends |= set(range(start + 1, stop + 1)) if styled else {stop}
    return ends


def in_figure(item, page):
    """A slide font finding inside a placed form XObject (an included figure), as a flag naming it."""
    box = item.get("bbox")
    for placed in page["placements"]:
        x0, y0, x1, y1 = placed["bbox"]
        if placed["kind"] == "form" and box and box[0] >= x0 - EDGE_TOLERANCE and box[1] >= y0 - EDGE_TOLERANCE \
                and box[2] <= x1 + EDGE_TOLERANCE and box[3] <= y1 + EDGE_TOLERANCE:
            return {**item, "severity": "flag" if item["severity"] == "fail" else item["severity"],
                    "in_figure": placed["name"]}
    return item


# Density (advisory)

def covered_area(rects, frame, cell=DENSITY_CELL):
    """Area of the union of rectangles inside `frame`, on a `cell`-pt raster."""
    columns = max(1, int((frame[2] - frame[0]) / cell + 0.5))
    rows = max(1, int((frame[3] - frame[1]) / cell + 0.5))
    mask = bytearray(columns * rows)
    for x0, y0, x1, y1 in rects:
        c0, c1 = max(0, int((x0 - frame[0]) / cell)), min(columns, int((x1 - frame[0]) / cell + 0.999))
        r0, r1 = max(0, int((y0 - frame[1]) / cell)), min(rows, int((y1 - frame[1]) / cell + 0.999))
        for row in range(r0, r1):
            if c1 > c0:
                mask[row * columns + c0:row * columns + c1] = b"\1" * (c1 - c0)
    return sum(mask) * cell * cell


def check_density(pages):
    """panel-narrow and page-underused flags, and the measured values per page."""
    findings, density, content = [], [], []
    for page in pages:
        blocks = defaultdict(list)
        for glyph in page["glyphs"]:
            blocks[glyph.block].append(glyph.vbox)
        rects = [union(b) for b in blocks.values()] + [p["bbox"] for p in page["placements"]]
        clip = (0, 0, page["width"], page["height"])
        rects = [r for r in ([max(r[0], 0), max(r[1], 0), min(r[2], clip[2]), min(r[3], clip[3])] for r in rects)
                 if r[2] > r[0] and r[3] > r[1]]
        content.append(rects)
    boxes = [union(rects) for rects in content if rects]
    inferred = union(boxes) if boxes else None
    area = lambda box: (box[2] - box[0]) * (box[3] - box[1])  # noqa: E731
    use_inferred = inferred is not None and len(pages) >= 3
    for number, (page, rects) in enumerate(zip(pages, content), 1):
        frame = inferred if use_inferred else [FRAME_INSET_PT, FRAME_INSET_PT, page["width"] - FRAME_INSET_PT,
                                               page["height"] - FRAME_INSET_PT]
        used = covered_area(rects, frame) / area(frame) if area(frame) > 0 else 0.0
        panels = []
        for placed in page["placements"]:
            if placed["kind"] != "form":
                continue
            x0, y0, x1, y1 = placed["bbox"]
            width, height = (x1 - x0) / 72 * 2.54, (y1 - y0) / 72 * 2.54
            panels.append({"name": placed["name"], "bbox": [round(v, 2) for v in placed["bbox"]],
                           "width_cm": round(width, 2), "height_cm": round(height, 2)})
            if width < PANEL_MIN_CM:
                findings.append(finding("panel-narrow", "flag",
                                        f"{placed['name']} is {width:.2f} cm wide (< {PANEL_MIN_CM:g} cm)",
                                        number, placed["bbox"], round(width, 2), figure_name=placed["name"]))
        if used < PAGE_USED_MIN:
            findings.append(finding("page-underused", "flag",
                                    f"text blocks and placed figures cover {used:.0%} of the "
                                    f"{'content frame' if use_inferred else 'page inset by 12 mm'} "
                                    f"(< {PAGE_USED_MIN:.0%})", number, frame, round(used, 3)))
        density.append({"page": number, "used_fraction": round(used, 3), "panels": panels, "frame": frame})
    return findings, {"frame": "content" if use_inferred else "page inset by 12 mm",
                      "content_frame": None if inferred is None else [round(v, 2) for v in inferred],
                      "pages": density}


def read_blank_exceptions(path):
    """Recorded blank-band exceptions ({raster_sha256: reason}) and findings for malformed entries."""
    if path is None:
        return {}, []
    try:
        items = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        return {}, [finding("blank-exceptions-invalid", "fail", f"{path}: unreadable JSON ({error})")]
    exceptions, findings = {}, []
    for item in items if isinstance(items, list) else [items]:
        digest = item.get("raster_sha256") if isinstance(item, dict) else None
        reason = item.get("reason") if isinstance(item, dict) else None
        if not (isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                and isinstance(reason, str) and reason.strip()):
            findings.append(finding("blank-exceptions-invalid", "fail",
                                    f"{path}: each entry needs raster_sha256 (64 hex) and a reason: {item!r}"))
            continue
        exceptions[digest] = reason.strip()
    return exceptions, findings


def check_blank_bands(pdf: Path, pages, density, limit, exceptions):
    """page-blank-band: the tallest run of ink-free raster rows across each page's density frame.

    Pages are rasterized in grey at BLANK_DPI; a row is blank when every pixel between the
    frame's left and right edges is at least BLANK_LEVEL. The band is measured inside the
    frame's vertical extent and reported as a fraction of the page height. A band above
    `limit` fails unless its page raster hash is a recorded exception (then `info` with the
    reason). The final page is measured but not checked: a document may end part-way down a page.
    """
    findings, used = [], set()
    ink = bytes(1 if level < BLANK_LEVEL else 0 for level in range(256))
    from PIL import Image
    with tempfile.TemporaryDirectory() as raw:
        subprocess.run(["pdftoppm", "-r", str(BLANK_DPI), "-gray", str(pdf), f"{raw}/p"], check=True)
        rendered = sorted(Path(raw).glob("p-*.pgm"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
        if len(rendered) != len(density["pages"]):
            raise SystemExit(f"pdftoppm rendered {len(rendered)} pages, extraction found {len(density['pages'])}")
        for path, extracted, page in zip(rendered, pages, density["pages"]):
            with Image.open(path) as image:
                width, height = image.size
                rows = image.convert("L").tobytes().translate(ink)
            x0, y0, x1, y1 = page.pop("frame")
            scale = height / extracted["height"]
            c0, c1 = max(0, int(x0 * scale)), min(width, int(x1 * scale + 0.999))
            r0, r1 = max(0, int(y0 * scale)), min(height, int(y1 * scale + 0.999))
            best, start, run = 0, r0, 0
            for row in range(r0, r1):
                run = run + 1 if b"\1" not in rows[row * width + c0:row * width + c1] else 0
                if run > best:
                    best, start = run, row - run + 1
            fraction = best / height
            page["blank_band"] = round(fraction, 3)
            if fraction <= limit or page["page"] == len(pages):  # the document's end may stay short
                continue
            digest = raster_sha256(path)
            box = [x0, start / scale, x1, (start + best) / scale]
            reason = exceptions.get(digest)
            if reason:
                used.add(digest)
            message = (f"blank band of {fraction:.0%} of the page height (> {limit:.0%}); "
                       f"page raster_sha256 {digest} at {BLANK_DPI} dpi")
            findings.append(finding("page-blank-band", "info" if reason else "fail", message, page["page"], box,
                                    round(fraction, 3), raster_sha256=digest,
                                    **({"exception": reason} if reason else {})))
    for digest in set(exceptions) - used:
        findings.append(finding("blank-exception-unmatched", "flag",
                                f"recorded exception {digest} ({exceptions[digest]}) matches no page "
                                f"with a blank band above {limit:.0%}", value=digest))
    return findings


# Figures, logs and fonts

def unwrap(text):
    """(first line number, logical line) pairs, rejoining TeX's 79-column wraps."""
    out, pending, start = [], "", None
    for number, line in enumerate(text.splitlines(), 1):
        start = start or number
        pending += line
        if len(line) != MAX_PRINT_LINE:
            out.append((start, pending))
            pending, start = "", None
    if pending:
        out.append((start, pending))
    return out


def resolve_include(name: str, bases) -> Path:
    """A TeX include name resolved against the first base that holds it (else the first base)."""
    candidates = [(base / name).resolve() for base in bases]
    return next((path for path in candidates if path.is_file()), candidates[0])


def log_figures(log: Path, bases=None):
    found = []
    for _, line in unwrap(log.read_text(errors="replace")):
        for name in re.findall(r"<([^<>,]+\.pdf), id=\d+", line):
            path = resolve_include(name, bases or [log.parent])
            if path not in found:
                found.append(path)
    return found


SIDECAR_SCHEMA, SIDECAR_VERSION = "analyb.figcheck", 1
SIDECAR_KEYS = {"check", "severity", "where", "bbox", "value", "message"}


def read_sidecar(data: bytes, figure_sha256: str):
    """Findings from an analyb sidecar's bytes, or the reason it cannot be trusted."""
    try:
        record = json.loads(data)
    except (OSError, ValueError) as error:
        return None, f"unreadable JSON ({error})"
    if not isinstance(record, dict) or (record.get("schema"), record.get("schema_version")) != (
            SIDECAR_SCHEMA, SIDECAR_VERSION):
        return None, f"expected schema {SIDECAR_SCHEMA} version {SIDECAR_VERSION}"
    if record.get("pdf_sha256") != figure_sha256:
        return None, f"pdf_sha256 {record.get('pdf_sha256')} does not match the figure ({figure_sha256})"
    items = record.get("findings")
    if not isinstance(items, list) or not all(isinstance(i, dict) and SIDECAR_KEYS <= set(i) for i in items):
        return None, "findings must be a list of objects with " + ", ".join(sorted(SIDECAR_KEYS))
    if not isinstance(record.get("bbox_units"), str):
        return None, "bbox_units is missing"
    return record, None


def check_figure(path: Path, used_on, figure_sha256):
    """Findings for one included figure, and the sha256 of the sidecar bytes that were read."""
    findings, sidecar_sha256 = [], None
    pages, _ = extract(path)
    for number, page in enumerate(pages, 1):
        findings += check_outside("figure-text-clipped", page["glyphs"], page["width"], page["height"],
                                  page=None, figure=str(path), figure_page=number, used_on_pages=used_on)
    sidecar = path.with_suffix(".figcheck.json")
    if sidecar.is_file():
        data = sidecar.read_bytes()
        sidecar_sha256 = hashlib.sha256(data).hexdigest()
        record, problem = read_sidecar(data, figure_sha256)
        if problem:
            findings.append(finding("figure-sidecar-stale", "fail", f"{sidecar.name} for {path}: {problem}",
                                    figure=str(path), source=str(sidecar), used_on_pages=used_on))
        else:
            for item in record["findings"]:
                # analyb boxes stay in their own units, never in the report's bbox.
                findings.append(fingerprinted({**item, "page": None, "bbox": None, "figure_bbox": item["bbox"],
                                               "figure_bbox_units": record["bbox_units"], "figure": str(path),
                                               "source": str(sidecar), "used_on_pages": used_on}))
    return findings, sidecar_sha256


LOG_PATTERNS = (
    (re.compile(r"Overfull \\([hv]box) \((-?[\d.]+)pt too (?:wide|high)\)(.*)"), "log-overfull"),
    (re.compile(r"Reference [`']([^']*)' on page (\d+) undefined"), "log-undefined-reference"),
    (re.compile(r"Citation [`']([^']*)'(?: on page (\d+))? undefined"), "log-undefined-citation"),
    (re.compile(r"There were undefined (?:references|citations)"), "log-undefined-reference"),
    (re.compile(r"may have changed|Rerun to get|[Rr]erun LaTeX|\(re\)run"), "log-rerun"),
    (re.compile(r"File [`']([^']+)' not found"), "log-missing-file"),
    (re.compile(r"^No file (\S+)\.$"), "log-missing-file"),
    (re.compile(r"^! (.*)"), "log-error"),
    (re.compile(r"^.+?\.(?:tex|sty|cls|ltx|def|cfg|clo|fd|dtx|bbl|aux|toc|lof|lot):\d+: (.*)"), "log-error"),
)


def check_log(log: Path):
    findings = []
    for number, line in unwrap(log.read_text(errors="replace")):
        for pattern, check in LOG_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            value, page, severity = None, None, "fail"
            if check == "log-overfull":
                value = float(match.group(2))
                severity = "fail" if value > 1.0 else "flag"
            elif check in ("log-undefined-reference", "log-undefined-citation") and match.groups():
                value = match.group(1)
                page = int(match.group(2)) if match.group(2) else None
            elif check == "log-missing-file":
                value = match.group(1)
                severity = "flag" if line.startswith("No file") else "fail"
            findings.append(finding(check, severity, line.strip(), page, None, value,
                                    source=f"{log}:{number}"))
            break
    return findings


def check_blg(blg: Path):
    findings = []
    for number, line in enumerate(blg.read_text(errors="replace").splitlines(), 1):
        match = re.search(r"\b(WARN|ERROR) - (.*)", line)
        if match:
            severity = "fail" if match.group(1) == "ERROR" else "flag"
            findings.append(finding("blg-" + match.group(1).lower(), severity, match.group(2).strip(),
                                    source=f"{blg}:{number}"))
    return findings


def pdf_fonts(pdf: Path):
    """(name, type, embedded) for every font pdffonts lists."""
    lines = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True, check=True).stdout.splitlines()
    if len(lines) < 2:
        return []
    columns = [(m.start(), m.end()) for m in re.finditer(r"-+", lines[1])]
    fonts = []
    for line in lines[2:]:
        cells = [line[a:b + 1].strip() if i < len(columns) - 1 else line[a:].strip()
                 for i, (a, b) in enumerate(columns)]
        fonts.append((cells[0], cells[1], cells[3]))
    return fonts


def check_pdffonts(pdf: Path):
    findings = []
    for name, kind, embedded in pdf_fonts(pdf):
        if embedded != "yes":
            findings.append(finding("font-not-embedded", "fail", f"{name} ({kind}) is not embedded", value=name))
        if kind == "Type 3":
            findings.append(finding("font-type3", "flag", f"{name} is a Type 3 font", value=name))
    return findings


def lint_report(args):
    """The lint-pdf report for parsed lint-pdf arguments."""
    pdf = args.pdf.resolve(strict=True)
    pdf_sha256 = sha256_file(pdf)  # bound before the PDF is read
    pages, embedded = extract(pdf)
    slides = args.profile == "slides"
    ends = frame_ends(pdf, len(pages)) if slides else set(range(1, len(pages) + 1))
    findings, page_fonts, suppressed, overlay_hidden = [], [], 0, 0
    for number, page in enumerate(pages, 1):
        glyphs = page["glyphs"]
        if number not in ends:
            shown = [g for g in glyphs if g.vbox[2] > 0 and g.vbox[3] > 0
                     and g.vbox[0] < page["width"] and g.vbox[1] < page["height"]]
            overlay_hidden += sum(1 for g in glyphs if g.text.strip()) - sum(1 for g in shown if g.text.strip())
            glyphs = shown
        font_findings, summary = check_fonts(number, glyphs, args.min_font_pt, args.flag_font_pt)
        findings += [in_figure(f, page) for f in font_findings] if slides else font_findings
        overlaps, hidden = check_overlap(number, glyphs)
        findings += overlaps
        suppressed += hidden
        findings += check_outside("text-off-page", glyphs, page["width"], page["height"], number)
        if page["ambiguous"]:
            findings.append(finding("extraction-ambiguous", "info",
                                    f"{page['ambiguous']} glyphs had conflicting paint records; they are "
                                    "checked as visible, unclipped and not sub/superscripts",
                                    number, value=page["ambiguous"]))
        page_fonts.append(summary)
    if slides:
        density = None
    else:
        density_findings, density = check_density(pages)
        findings += density_findings
        exceptions, findings_invalid = read_blank_exceptions(args.blank_exceptions)
        findings += findings_invalid
        findings += check_blank_bands(pdf, pages, density, args.max_blank_band, exceptions)
    bases = [args.log.parent, pdf.parent] if args.log else [pdf.parent]
    used = defaultdict(set)
    for number, names in enumerate(embedded, 1):
        for name in names:
            used[resolve_include(name, bases)].add(number)
    if args.log:
        findings += check_log(args.log)
    if args.no_figure_check:
        figures = []
        findings.append(finding("figure-check-skipped", "info",
                                f"figure checks skipped by --no-figure-check ({len(used)} included figures)",
                                value=len(used)))
    elif args.figure:
        figures = [p.resolve(strict=True) for p in args.figure]
    else:
        named = list(dict.fromkeys([*used, *(log_figures(args.log, bases) if args.log else [])]))
        figures = [p for p in named if p.is_file()]
        for path in named:
            if path not in figures:
                findings.append(finding("figure-unresolved", "fail",
                                        f"included figure {path} is not on disk, so it cannot be checked",
                                        value=str(path), used_on_pages=sorted(used.get(path, ()))))
    figure_records = []
    for path in figures:
        digest = sha256_file(path)  # bound before the figure is read
        figure_findings, sidecar_sha256 = check_figure(path, sorted(used.get(path, ())), digest)
        findings += figure_findings
        figure_records.append({"path": str(path), "sha256": digest, "sidecar_sha256": sidecar_sha256,
                               "used_on_pages": sorted(used.get(path, ()))})
    if args.blg:
        findings += check_blg(args.blg)
    findings += check_pdffonts(pdf)
    counts = defaultdict(Counter)
    for item in findings:
        counts[item["severity"]][item["check"]] += 1
    report = {
        "command": "lint-pdf", "pdf": str(pdf), "sha256": pdf_sha256, "pages": len(pages),
        "profile": args.profile, "frames": len(ends) if slides else None,
        "min_font_pt": args.min_font_pt, "flag_font_pt": args.flag_font_pt,
        "blank_band": None if slides else {"max_fraction": args.max_blank_band, "dpi": BLANK_DPI,
                                           "level": BLANK_LEVEL},
        "inputs": {"log": str(args.log) if args.log else None, "blg": str(args.blg) if args.blg else None,
                   "blank_exceptions": str(args.blank_exceptions) if args.blank_exceptions else None},
        "tools": {"mutool": tool_version(["mutool", "-v"]), "pdffonts": tool_version(["pdffonts", "-v"]),
                  "pdftoppm": tool_version(["pdftoppm", "-v"])},
        "counts": {**{severity: dict(sorted(c.items())) for severity, c in sorted(counts.items())},
                   "suppressed": {"text-overlap": suppressed, "overlay-hidden": overlay_hidden}},
        "extraction": {"invisible_glyphs": sum(p["invisible"] for p in pages),
                       "unmatched_glyphs": sum(p["unmatched"] for p in pages),
                       "ambiguous_glyphs": sum(p["ambiguous"] for p in pages)},
        "page_fonts": page_fonts, "density": density, "figures": figure_records, "findings": findings,
    }
    return report


def lint_pdf(args):
    report = lint_report(args)
    emit(report, args.json)
    return 1 if report["counts"].get("fail") else 0


def emit(report, out):
    text = json.dumps(report, indent=2) + "\n"
    if out:
        out.write_text(text)
        print(json.dumps({k: report[k] for k in ("command", "counts") if k in report}))
    else:
        sys.stdout.write(text)


# Review packet

TILE, GAP, LABEL = 400, 8, 30  # contact-sheet thumbnail box, spacing and label strip in px


def pil_version():
    import PIL
    return PIL.__version__


def contact_sheet(tiles, columns, rows, target):
    """Tile labelled page thumbnails, at most TILE px on a side, on a grey sheet."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:  # Pillow < 10.1
        font = ImageFont.load_default()
    cell_w, cell_h = TILE + 2 * GAP, TILE + LABEL + 2 * GAP
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "#dddddd")
    draw = ImageDraw.Draw(sheet)
    for index, (path, label) in enumerate(tiles):
        x, y = index % columns * cell_w, index // columns * cell_h
        with Image.open(path) as image:
            thumb = image.convert("RGB")
        thumb.thumbnail((TILE, TILE))
        sheet.paste(thumb, (x + GAP + (TILE - thumb.width) // 2, y + GAP + (TILE - thumb.height) // 2))
        draw.text((x + cell_w // 2, y + GAP + TILE + LABEL // 2), label, fill="black", font=font, anchor="mm")
    sheet.save(target)


def packet(args):
    manifest = build_packet(args.pdf, args.out, args.dpi, args.sheet, args.force)
    print(json.dumps({"out": str(args.out), "pages": manifest["page_count"],
                      "contact_sheets": len(manifest["contact_sheets"])}))
    return 0


def build_packet(pdf, out, dpi, sheet, force=False):
    """Write page PNGs, contact sheets and manifest.json into `out`; return the manifest."""
    pdf = pdf.resolve(strict=True)
    if out.exists() and any(out.iterdir()):
        if not force:
            raise SystemExit(f"refusing to write into non-empty {out}; pass --force")
        for stale in [*out.glob("page-*.png"), *out.glob("contact-*.png"), out / "manifest.json"]:
            stale.unlink(missing_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    columns, rows = map(int, sheet.lower().split("x"))
    with tempfile.TemporaryDirectory(dir=out) as raw:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), f"{raw}/raw"], check=True)
        rendered = sorted(Path(raw).glob("raw-*.png"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
        images = []
        for number, path in enumerate(rendered, 1):
            target = out / f"page-{number:03d}.png"
            shutil.move(path, target)
            from PIL import Image
            with Image.open(target) as image:
                size = image.size
            images.append({"page": number, "png": target.name, "png_sha256": sha256_file(target),
                           "raster_sha256": raster_sha256(target), "width_px": size[0], "height_px": size[1]})
    sheets, per_sheet = [], columns * rows
    for start in range(0, len(images), per_sheet):
        chunk = images[start:start + per_sheet]
        target = out / f"contact-{start // per_sheet + 1:02d}.png"
        contact_sheet([(out / item["png"], f"page {item['page']}") for item in chunk], columns, rows, target)
        sheets.append({"png": target.name, "pages": [item["page"] for item in chunk],
                       "png_sha256": sha256_file(target)})
    manifest = {
        "pdf": str(pdf), "size": pdf.stat().st_size, "sha256": sha256_file(pdf),
        "page_count": len(images), "dpi": dpi, "sheet": f"{columns}x{rows}",
        "tools": {"pdftoppm": tool_version(["pdftoppm", "-v"]), "PIL": pil_version()},
        "pages": images, "contact_sheets": sheets,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


# Carry-over decision

def changed_region(old_png: Path, new_png: Path, dpi):
    from PIL import Image, ImageChops
    with Image.open(old_png) as old, Image.open(new_png) as new:
        if old.size != new.size:
            box = (0, 0, new.width, new.height)
        else:
            box = ImageChops.difference(old.convert("RGB"), new.convert("RGB")).getbbox()
    if box is None:
        return None, None
    return list(box), [round(v * 72 / dpi, 2) for v in box]


def manifest_problem(path: Path, manifest):
    """Why a packet manifest cannot be trusted, or None. Hashes are recomputed from the PNGs."""
    pages = manifest.get("pages")
    if not isinstance(pages, list) or manifest.get("page_count") != len(pages) or not pages:
        return f"{path}: page_count {manifest.get('page_count')} does not match {len(pages or [])} page entries"
    for number, item in enumerate(pages, 1):
        if item.get("page") != number:
            return f"{path}: entry {number} is page {item.get('page')}; pages must be numbered 1..N in order"
        png = path.parent / str(item.get("png"))
        if not png.is_file():
            return f"{path}: page {number} image {png} is missing"
        if raster_sha256(png) != item.get("raster_sha256"):
            return f"{path}: page {number} raster hash does not match {png.name} on disk"
    return None


class Refused(RuntimeError):
    pass


def diff(args):
    try:
        report = diff_report(args.old, args.new, args.reviewed)
    except Refused as error:
        print(f"refusing to compare: {error}", file=sys.stderr)
        return 2
    emit(report, args.json)
    return 0


def diff_report(old_path, new_path, reviewed_path):
    """Carry-over decisions between two packet manifests; raises Refused."""
    old_path, new_path = old_path.resolve(strict=True), new_path.resolve(strict=True)
    old, new = json.loads(old_path.read_text()), json.loads(new_path.read_text())
    for path, manifest in ((old_path, old), (new_path, new)):
        problem = manifest_problem(path, manifest)
        if problem:
            raise Refused(problem)
    if old["dpi"] != new["dpi"]:
        raise Refused(f"rasters at different DPI: {old['dpi']} vs {new['dpi']}")
    reviewed = {item["raster_sha256"]: item["verdict_ref"] for item in json.loads(reviewed_path.read_text())}
    pages = []
    old_by_hash = {item["raster_sha256"]: item for item in old["pages"]}
    for after in new["pages"]:
        digest = after["raster_sha256"]
        before = old_by_hash.get(digest)
        entry = {"page": after["page"], "raster_sha256": digest}
        if before is not None and digest in reviewed:
            entry.update(decision="carry", old_page=before["page"], verdict_ref=reviewed[digest])
        elif before is not None:
            entry.update(decision="unreviewed", reason="identical raster has no recorded review")
        else:
            entry.update(decision="changed", reason="new raster has no identical page in the old packet")
            # Positional localization is only meaningful while page counts agree.
            # The exact hash carry decision above does not depend on this pointer.
            if old["page_count"] == new["page_count"] and after["page"] <= len(old["pages"]):
                prior = old["pages"][after["page"] - 1]
                entry["changed_bbox_px"], entry["changed_bbox_pt"] = changed_region(
                    old_path.parent / prior["png"], new_path.parent / after["png"], new["dpi"])
        pages.append(entry)
    needing = {p["page"] for p in pages if p["decision"] == "changed"}
    for entry in pages:
        if entry["decision"] == "carry" and needing & {entry["page"] - 1, entry["page"] + 1}:
            entry.update(decision="neighbour", reason="next to a changed page")
    report = {
        "command": "diff", "old": str(old_path), "new": str(new_path), "dpi": new["dpi"],
        "old_pdf_sha256": old["sha256"], "new_pdf_sha256": new["sha256"],
        "review_pages": [p["page"] for p in pages if p["decision"] != "carry"],
        "carried_pages": [p["page"] for p in pages if p["decision"] == "carry"],
        "pages": pages,
        "note": "Exact page appearance carries across movement. Check sequence, pagination and routes "
                "separately; candidate pages are not a mandate for exhaustive model inspection.",
    }
    return report


# Printed values (copy of analyb.printed's matching rule; analyb is not imported)

VALUES_SCHEMA, VALUES_VERSION = "analyb.printed_values", 4
MATCH_RULE = (
    "v4; fold unary minus U+2212 U+FE63 U+FF0D to '-' and Unicode decimal digits "
    "to ASCII; preserve dash U+2012 U+2013 U+2010 U+2011 U+2014 as separators "
    "and treat ASCII '-' runs as placeholders; "
    "one maximal-candidate scanner for line and record text: optional unary '+' "
    "or '-' with zero or one non-tab, non-linebreak whitespace character after "
    "it; a longer sign gap is ambiguous and rejects the following candidate; "
    "a sign directly after a word, '.', ')' or another sign is invalid; a sign "
    "directly after a numeric candidate without whitespace on either side is "
    "a compact range separator; a spaced sign after a numeric candidate with "
    "at most one intervening whitespace character is ambiguous and rejected; "
    "mantissa digits with optional '.'+digits, or leading '.'+digits; grouping "
    "commas allow whitespace on both sides and require a first group of one to "
    "three digits and subsequent groups of exactly three digits, before the "
    "fraction; optional exponent e/E, optional sign and digits with whitespace "
    "around e/E and its sign; optional suffix with any preceding whitespace: "
    "% GeV MeV TeV keV eV fb-1 pb-1 fb pb nb mb mm cm rad mrad ns ps; "
    "malformed groups, fractions or exponents, nondecimal numerals, attached "
    "unsupported words and word-adjacent candidates are consumed and rejected "
    "whole, never rescanned inside; canonical form removes whitespace; record "
    "text containing any numeric character outside accepted spans fails; an "
    "exactly one-token text matches an equal canonical line token; other text "
    "matches its characters in order with optional whitespace (dash glyphs "
    "fold to '-' only for this literal comparison), Unicode decimal boundaries, "
    "and every text token also present as a complete line token; context on the "
    "same line matches whole Unicode word boundaries, with '_' and whitespace "
    "interchangeable; only row presence, not cells or arithmetic, is verified"
)

_MINUS = str.maketrans({c: "-" for c in "\u2212\ufe63\uff0d"})
_DASH = str.maketrans({c: "-" for c in "\u2012\u2013\u2010\u2011\u2014"})
_UNITS = ("fb-1", "pb-1", "mrad", "GeV", "MeV", "TeV", "keV", "eV", "rad",
          "fb", "pb", "nb", "mb", "mm", "cm", "ns", "ps", "%")
# Candidate consumption is deliberately broader than this supported grammar.
# Validate only after consumption, so a malformed token cannot expose a prefix.
_TOKEN = re.compile(
    r"[+-]?(?:(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?|\.[0-9]+)"
    r"(?:[eE][+-]?[0-9]+)?(?:" + "|".join(re.escape(u) for u in _UNITS) + r")?"
)


def normalize_text(text):
    """Fold unary minus glyphs and decimal digits, preserving dash identity."""
    return "".join(str(unicodedata.decimal(c)) if c.isdecimal() else c
                   for c in text.translate(_MINUS))


def _word(c):
    return c.isalnum() or c == "_"


def _skip_space(s, i):
    while i < len(s) and s[i].isspace():
        i += 1
    return i


def _digits(s, i):
    # Consume unsupported numerals too, so no interior fragment can reappear.
    while i < len(s) and s[i].isnumeric():
        i += 1
    return i


def _numeric_start(s, i):
    return i < len(s) and (s[i].isnumeric() or (
        s[i] == "." and i + 1 < len(s) and s[i + 1].isnumeric()))


def _numeric_end(s, i):
    if i < len(s) and s[i] == ".":
        i += 1
    return _digits(s, i)


def _sign_end(s, i):
    while i < len(s) and s[i] in "+-":
        i = _skip_space(s, i + 1)
    return i


def _number_at(s, i, previous_end):
    """Consume one maximal candidate; return its end and whether it is supported."""
    j, valid = i, True
    if s[j] in "+-":
        j = _sign_end(s, j)
        gap = s[i + 1:j]
        valid = (len(gap) <= 1 and not any(c in "\t\r\n" for c in gap)
                 and not (i > 0 and (_word(s[i - 1]) or s[i - 1] in ".)+-")))
        # PDF extraction cannot distinguish a binary minus from a spaced unary
        # sign in neighbouring cells. Reject the ambiguous operand as a whole.
        if (gap and previous_end is not None and i - previous_end <= 1
                and not s[previous_end:i].strip()):
            valid = False
    elif i > 0 and (_word(s[i - 1]) or s[i - 1] == "."):
        valid = False

    end = _numeric_end(s, j)
    suffix = False
    while end < len(s):
        k = _skip_space(s, end)
        if k < len(s) and s[k] == ",":
            # Include malformed comma runs and signed groups in the candidate.
            start = k
            while start < len(s) and s[start] == ",":
                start = _skip_space(s, start + 1)
            start = _sign_end(s, start)
            if _numeric_start(s, start):
                end = _numeric_end(s, start)
                continue
            break  # A prose comma, not a numeric continuation.
        if s[end] == ".":
            start = end
            while start < len(s) and s[start] == ".":
                start += 1
            if start < len(s) and s[start].isnumeric():
                end = _digits(s, start)
                continue
        if k < len(s) and s[k] in "eE":
            start = _skip_space(s, k + 1)
            signed = start < len(s) and s[start] in "+-"
            if signed:
                start = _sign_end(s, start)
            # eV is a suffix, while even an incomplete or repeated exponent
            # must be consumed before the supported grammar is checked.
            if (signed or _numeric_start(s, start) or start == len(s)
                    or not _word(s[start])):
                end = _numeric_end(s, start)
                continue
        if not suffix:
            for unit in _UNITS:
                stop = k + len(unit)
                # Consume even a suffix with an attached invalid continuation;
                # the full grammar must reject it without exposing a prefix.
                # An alphabetic prefix of a separate word is not a unit.
                if s.startswith(unit, k) and (k == end or not unit.isalpha()
                                             or stop == len(s) or not _word(s[stop])):
                    end, suffix = stop, True
                    break
            else:
                stop = None
            if stop is not None:
                continue
        if _word(s[end]):
            # Consume attached unknown words one character at a time so a
            # later e+digits continuation is swallowed too, not rescanned.
            end += 1
            continue
        break
    return end, valid and _TOKEN.fullmatch(_canonical(s[i:end])) is not None


def _scan(s):
    """Accepted (start, end) spans; rejected candidates are consumed whole."""
    spans, i, previous_end = [], 0, None
    while i < len(s):
        start = _sign_end(s, i)
        if s[i] == "-" and i + 1 < len(s) and s[i + 1] == "-":
            # A run of ASCII dashes is a placeholder, never a unary sign.
            while i < len(s) and s[i] == "-":
                i += 1
            continue
        if s[i] in "+-" and previous_end == i and start == i + 1:
            # Compact range (0-5), not a signed right-hand endpoint.
            i += 1
            continue
        if _numeric_start(s, start):
            end, valid = _number_at(s, i, previous_end)
            if valid:
                spans.append((i, end))
            previous_end = end if valid else None
            i = end
        else:
            i += 1
    return spans


def _canonical(token):
    return re.sub(r"\s+", "", token)


def numeric_tokens(line):
    """Canonical numeric tokens of ``line`` (see ``MATCH_RULE``)."""
    line = normalize_text(line)
    return [_canonical(line[a:b]) for a, b in _scan(line)]


def numeric_text(text):
    """Canonical form if ``text`` is exactly one numeric token, else None."""
    stripped = normalize_text(text).strip()
    spans = _scan(stripped)
    if len(spans) == 1 and spans[0] == (0, len(stripped)):
        return _canonical(stripped)
    return None


def text_pattern(text):
    """Pattern for non-numeric ``text``: characters in order, optional whitespace."""
    chars = [re.escape(c) for c in normalize_text(text).translate(_DASH) if not c.isspace()]
    if not chars:
        raise ValueError("printed text must contain a non-space character")
    return re.compile(r"(?<![\d.])" + r"\s*".join(chars) + r"(?!\d|\.\d)")


def context_pattern(context):
    """Pattern for a ``context`` label as a whole token sequence.

    Each whitespace run or ``_`` matches whitespace or ``_`` (pdflatex's
    default encoding extracts an escaped ``_`` as a space); the label may not
    continue into a neighbouring letter, digit or ``_``.
    """
    parts = re.split(r"(\s+|_)", normalize_text(context).strip())
    body = "".join(r"(?:\s+|_)" if part.isspace() or part == "_" else re.escape(part)
                   for part in parts if part)
    if not re.search(r"[^\W_]", context):
        raise ValueError("context must contain a letter or digit")
    return re.compile(r"(?<!\w)" + body + r"(?!\w)")


def find_printed(lines, text, context=None):
    """Return indices of ``lines`` where ``text`` (and ``context``, if given) match."""
    text = normalize_text(text).strip()
    spans = _scan(text)
    # Literal matching must never bypass a rejected number (e.g. 12kg).
    if any(c.isnumeric() and not any(a <= i < b for a, b in spans)
           for i, c in enumerate(text)):
        return []
    parts = [_canonical(text[a:b]) for a, b in spans]
    if len(spans) == 1 and spans[0] == (0, len(text)):
        matches = lambda line: parts[0] in numeric_tokens(line)  # noqa: E731
    else:
        pattern = text_pattern(text)

        def matches(line):
            tokens = numeric_tokens(line)
            return (bool(pattern.search(line.translate(_DASH)))
                    and all(part in tokens for part in parts))
    context_re = context_pattern(context) if context else None
    hits = []
    for index, line in enumerate(lines):
        line = normalize_text(line)
        if matches(line) and (context_re is None or context_re.search(line)):
            hits.append(index)
    return hits


def page_texts(pdf: Path, layout=True):
    """Per-page text from pdftotext (with -layout by default)."""
    command = ["pdftotext", *(["-layout"] if layout else []), str(pdf), "-"]
    text = subprocess.run(command, capture_output=True, text=True, check=True).stdout
    pages = text.split("\f")
    return pages[:-1] if pages and not pages[-1].strip() else pages


def resolve(base: Path, name):
    path = Path(name)
    return (path if path.is_absolute() else base / path).resolve()


def numbers_report(pdf: Path, manifest_path: Path):
    """Check that every printed value in an analyb manifest appears in the PDF."""
    pdf, manifest_path = pdf.resolve(strict=True), manifest_path.resolve(strict=True)
    pdf_sha256, data = sha256_file(pdf), manifest_path.read_bytes()
    report = {"command": "numbers", "pdf": str(pdf), "sha256": pdf_sha256, "manifest": str(manifest_path),
              "manifest_sha256": hashlib.sha256(data).hexdigest(), "sources": [], "findings": []}
    findings = report["findings"]
    try:
        manifest = json.loads(data)
    except (ValueError, UnicodeError):
        manifest = None
    if not isinstance(manifest, dict) or \
            (manifest.get("schema"), manifest.get("schema_version")) != (VALUES_SCHEMA, VALUES_VERSION) \
            or manifest.get("match_rule") != MATCH_RULE or not isinstance(manifest.get("values"), list) \
            or not isinstance(manifest.get("sources"), dict):
        findings.append(finding("values-invalid", "fail",
                                f"{manifest_path} is not {VALUES_SCHEMA} version {VALUES_VERSION} with this match rule"))
        return report
    sources = manifest["sources"]
    for role, source in sources.items():
        if not isinstance(source, dict) or not isinstance(source.get("path"), str) or not source["path"] \
                or not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            findings.append(finding("values-invalid", "fail", f"source {role!r} needs a path and SHA-256", value=role))
            continue
        try:
            path = resolve(manifest_path.parent, source["path"])
            _, binding = read_bound(path)
        except (OSError, ValueError):
            binding = None
        if binding:
            report["sources"].append({"role": role, **binding})
        if not binding or binding["sha256"] != source["sha256"]:
            findings.append(finding("source-stale", "fail",
                                    f"source {role!r} ({source['path']}) is missing or no longer has sha256 {source['sha256']}",
                                    value=role))
    pages = [text.splitlines() for text in page_texts(pdf)]
    matched = 0
    for index, record in enumerate(manifest["values"]):
        if not isinstance(record, dict) or not all(isinstance(record.get(k), str) and record[k]
                                                  for k in ("key", "text")) \
                or any(record.get(k) is not None and not isinstance(record[k], str)
                       for k in ("context", "section", "source")) \
                or (record.get("page") is not None and
                    (type(record["page"]) is not int or record["page"] <= 0)) \
                or (record.get("source") is not None and record["source"] not in sources):
            findings.append(finding("values-invalid", "fail",
                                    f"value record {index + 1} needs text/key strings, a positive integer page or null, "
                                    "and a registered source or null", value=index + 1))
            continue
        try:
            text_pattern(record["text"])
            if record.get("context") is not None:
                context_pattern(record["context"])
        except ValueError as error:
            findings.append(finding("values-invalid", "fail",
                                    f"value record {index + 1}: {error}", value=index + 1))
            continue
        wanted = [record["page"]] if record.get("page") is not None else range(1, len(pages) + 1)
        hits = [(page, line) for page in wanted if page <= len(pages)
                for line in find_printed(pages[page - 1], record["text"], record.get("context"))]
        where = f"{record['text']!r}" + (f" with context {record['context']!r}" if record.get("context") else "") \
            + (f" on page {record['page']}" if record.get("page") is not None else "")
        if not hits:
            findings.append(finding("value-missing", "fail", f"{record['key']}: {where} not found",
                                    record.get("page"), value=record["text"], key=record["key"]))
        elif len(hits) > 1:
            findings.append(finding("value-ambiguous", "flag",
                                    f"{record['key']}: {where} matches {len(hits)} lines",
                                    value=record["text"], key=record["key"],
                                    hits=[{"page": page, "line": line + 1} for page, line in hits]))
        else:
            matched += 1
    report.update(values=len(manifest["values"]), matched_once=matched)
    return report


def numbers(args):
    report = numbers_report(args.pdf, args.manifest)
    emit_findings(report, args.json)
    return 1 if any(f["severity"] == "fail" for f in report["findings"]) else 0


# Page inventory

PAGEMAP_SCHEMA, PAGEMAP_VERSION = "analyb.plotbook_page_map", 1


def flat(text):
    """Whitespace-collapsed, minus-folded text; line-end hyphens joined in a second variant."""
    text = normalize_text(text).translate(_DASH)
    return " ".join(text.split()), " ".join(re.sub(r"-\s*\n\s*", "", text).split())


def tokens(text):
    return re.findall(r"[A-Za-z0-9]+", text)


def plan_matches(item, slot):
    if "figure" in item:
        return slot["figure"] == item["figure"]
    key, stem = tokens(item["key"]), tokens(Path(slot["figure"]).stem)
    return any(stem[i:i + len(key)] == key for i in range(len(stem) - len(key) + 1))


def valid_pagemap(record):
    """The producer emits ordered pages and consecutive two-column slots."""
    if not isinstance(record, dict) or \
            (record.get("schema"), record.get("schema_version")) != (PAGEMAP_SCHEMA, PAGEMAP_VERSION) \
            or type(record.get("page_count")) is not int or record["page_count"] < 0 \
            or not isinstance(record.get("pages"), list):
        return False
    entries = record["pages"]
    if len(entries) != record["page_count"]:
        return False
    for number, entry in enumerate(entries, 1):
        if not isinstance(entry, dict) or type(entry.get("page")) is not int or entry["page"] != number \
                or not isinstance(entry.get("section"), str) or type(entry.get("rows")) is not int \
                or entry["rows"] not in (2, 3) or not isinstance(entry.get("slots"), list) \
                or not 1 <= len(entry["slots"]) <= 2 * entry["rows"]:
            return False
        for index, slot in enumerate(entry["slots"]):
            if not isinstance(slot, dict) or not isinstance(slot.get("figure"), str) or not slot["figure"] \
                    or not isinstance(slot.get("caption"), str) \
                    or type(slot.get("row")) is not int or slot["row"] != index // 2 + 1 \
                    or type(slot.get("column")) is not int or slot["column"] != index % 2 + 1:
                return False
    return True


def slot_placements(page, base):
    """Physical rows share the figure-bottom baseline in the producer's [t] minipages.

    Column centres lie on either side of the page centre. Using figure bottoms
    also handles different aspect ratios in a row without assuming equal tops.
    """
    placed = [p for p in page["placements"] if p["ptex"]]
    bottoms = []
    for panel in sorted(placed, key=lambda p: p["bbox"][3]):
        bottom = panel["bbox"][3]
        if not bottoms or bottom - bottoms[-1] > 1:
            bottoms.append(bottom)
    return [{**p, "path": resolve(base, p["name"]),
             "row": min(range(len(bottoms)), key=lambda i: abs(bottoms[i] - p["bbox"][3])) + 1,
             "column": 1 if (p["bbox"][0] + p["bbox"][2]) / 2 < page["width"] / 2 else 2}
            for p in placed]


def region_text(page, region, panels):
    """Exact text in a label region, excluding glyphs inside the placed figures.

    MuPDF lines are kept in reading order, with line breaks retained for the
    same whitespace and line-end-hyphen normalization as the inventory labels.
    """
    lines = defaultdict(list)
    for glyph in page["glyphs"]:
        x = (glyph.bbox[0] + glyph.bbox[2]) / 2
        y = (glyph.bbox[1] + glyph.bbox[3]) / 2
        if region[0] <= x <= region[2] and region[1] <= y <= region[3] \
                and not any(p["bbox"][0] <= x <= p["bbox"][2] and p["bbox"][1] <= y <= p["bbox"][3]
                            for p in panels):
            lines[glyph.line].append(glyph)
    return "\n".join("".join(g.text for g in glyphs) for _, glyphs in
                     sorted(lines.items(), key=lambda item: (min(g.bbox[1] for g in item[1]),
                                                            min(g.bbox[0] for g in item[1]))))


def inventory_labels(page, entry, panels, findings):
    """Check the producer's heading and each caption in its own column/row region."""
    number = entry["page"]
    top = min((p["bbox"][1] for p in panels), default=page["height"] - FRAME_INSET_PT)
    labels = [(entry["section"], "heading-missing", [FRAME_INSET_PT, FRAME_INSET_PT,
                                                  page["width"] - FRAME_INSET_PT, top], None)]
    for slot in entry["slots"]:
        hosts = [p for p in panels if (p["row"], p["column"]) == (slot["row"], slot["column"])
                 and p["path"] == slot["path"]]
        # Without its figure, a caption cannot be assigned to this slot.
        if len(hosts) != 1:
            findings.append(finding("caption-missing", "fail",
                                    f"{slot['caption']!r} cannot be tied to one figure in its slot on page {number}",
                                    number, value=slot["caption"], expected_figure=str(slot["path"])))
            continue
        panel = hosts[0]
        end = min((p["bbox"][1] for p in panels if p["row"] > panel["row"]),
                  default=page["height"] - FRAME_INSET_PT)
        # 0.485 textwidth minipages separated by hfill, from write_compact_plotbook.
        width = 0.485 * (page["width"] - 2 * FRAME_INSET_PT)
        left = FRAME_INSET_PT if panel["column"] == 1 else page["width"] - FRAME_INSET_PT - width
        labels.append((slot["caption"], "caption-missing", [left, panel["bbox"][3], left + width, end],
                       str(slot["path"])))
    for label, check, region, figure in labels:
        actual = region_text(page, region, panels)
        if not set(flat(label)).intersection(flat(actual)):
            findings.append(finding(check, "fail", f"{label!r} is not the exact text in its region on page {number}",
                                    number, bbox=region, value=label, expected_figure=figure, actual_text=actual))


def inventory_report(pdf: Path, map_path: Path, plan_path=None):
    """Compare the compiled PDF with the producer's declared two-column slots."""
    pdf, map_path = pdf.resolve(strict=True), map_path.resolve(strict=True)
    pdf_sha256, data = sha256_file(pdf), map_path.read_bytes()
    report = {"command": "inventory", "pdf": str(pdf), "sha256": pdf_sha256, "pagemap": str(map_path),
              "pagemap_sha256": hashlib.sha256(data).hexdigest(), "findings": []}
    findings = report["findings"]
    try:
        record = json.loads(data)
    except (ValueError, UnicodeError):
        record = None
    if not valid_pagemap(record):
        findings.append(finding("pagemap-invalid", "fail",
                                f"{map_path} needs {PAGEMAP_SCHEMA} version {PAGEMAP_VERSION}, pages 1..page_count "
                                "in order, and consecutive row/column slots"))
        return report
    base = map_path.parent
    pages, _ = extract(pdf)
    if record.get("pdf") and record["pdf"] != pdf.name:
        findings.append(finding("pagemap-pdf-name", "flag", f"the map describes {record['pdf']}, not {pdf.name}",
                                value=record["pdf"]))
    if record["page_count"] != len(pages):
        findings.append(finding("page-count", "fail",
                                f"the PDF has {len(pages)} pages; the map expects {record['page_count']}",
                                value=[len(pages), record["page_count"]]))
    for entry in record["pages"]:
        number = entry["page"]
        if number > len(pages):
            continue
        page = pages[number - 1]
        try:
            expected = [resolve(base, slot["figure"]) for slot in entry["slots"]]
            panels = slot_placements(page, base)
        except (OSError, ValueError):
            findings.append(finding("pagemap-invalid", "fail", "figure paths must be valid paths", number))
            continue
        placed = [p["path"] for p in panels]
        missing = [str(p) for p in expected if expected.count(p) > placed.count(p)]
        extra = [str(p) for p in placed if placed.count(p) > expected.count(p)]
        for path in dict.fromkeys(missing):
            findings.append(finding("figure-missing", "fail", f"{path} is mapped to page {number} but not placed there",
                                    number, value=path))
        for path in dict.fromkeys(extra):
            findings.append(finding("figure-extra", "fail", f"{path} is placed on page {number} but not mapped there",
                                    number, value=path))
        if not missing and not extra:
            if placed != expected:
                findings.append(finding("figure-misordered", "fail", f"page {number} places the mapped figures in a "
                                        "different order", number, value=[str(p) for p in placed]))
            physical = [(p["row"], p["column"], p["path"]) for p in panels]
            intended = [(slot["row"], slot["column"], path) for slot, path in zip(entry["slots"], expected)]
            if Counter(physical) != Counter(intended):
                findings.append(finding("figure-misplaced", "fail", f"page {number} places figures in different "
                                        "row/column slots", number,
                                        value=[[row, column, str(path)] for row, column, path in physical]))
        labelled = {**entry, "slots": [{**slot, "path": path} for slot, path in zip(entry["slots"], expected)]}
        inventory_labels(page, labelled, panels, findings)
    if plan_path:
        plan_path = plan_path.resolve(strict=True)
        plan_data = plan_path.read_bytes()
        report.update(plan=str(plan_path), plan_sha256=hashlib.sha256(plan_data).hexdigest())
        try:
            plan = json.loads(plan_data)
        except (ValueError, UnicodeError):
            plan = None
        if not isinstance(plan, list) or any(not isinstance(item, dict) or
                not any(isinstance(item.get(k), str) and item[k] for k in ("figure", "key")) or
                any(k in item and (not isinstance(item[k], str) or not item[k]) for k in ("figure", "key")) or
                (item.get("group") is not None and not isinstance(item["group"], str)) for item in plan):
            findings.append(finding("plan-invalid", "fail", "coverage plan needs a list of figure/key items"))
            return report
        slots = [(entry["page"], slot) for entry in record["pages"] for slot in entry["slots"]]
        groups = defaultdict(set)
        for item in plan:
            hosts = {page for page, slot in slots if plan_matches(item, slot)}
            label = item.get("figure") or item.get("key")
            if not hosts:
                findings.append(finding("coverage-missing", "fail", f"required {label!r} is not in the page map",
                                        value=label))
            if item.get("group"):
                groups[item["group"]].update(hosts)
        for group, hosts in groups.items():
            if len(hosts) > 1:
                findings.append(finding("group-split", "flag", f"group {group!r} spans pages {sorted(hosts)}",
                                        value=sorted(hosts), group=group))
    return report


def inventory(args):
    report = inventory_report(args.pdf, args.pagemap, args.plan)
    emit_findings(report, args.json)
    return 1 if any(f["severity"] == "fail" for f in report["findings"]) else 0


def emit_findings(report, out):
    counts = defaultdict(Counter)
    for item in report["findings"]:
        counts[item["severity"]][item["check"]] += 1
    report["counts"] = {severity: dict(sorted(c.items())) for severity, c in sorted(counts.items())}
    emit(report, out)


# Gate: bind inputs, run the checks, decide whether visual review may start

def file_record(path):
    return None if path is None else {"path": str(path.resolve()), "sha256": sha256_file(path),
                                      "size": path.stat().st_size}


WAIVER_KEYS = ("id", "check", "fingerprint", "reason", "approved_by")
APPROVAL_RE = re.compile(r"^\s*(?:[-*]\s*)?waiver (\S+): (.+) \(approved by ([^,()]+), (\d{4}-\d{2}-\d{2})\)\s*$")


def read_waivers(data, state, approver=None):
    """Split waivers.json entries into usable, invalid and unapproved ones.

    An entry needs `id`, `check`, `fingerprint` (of one finding), `reason`,
    `approved_by` and exactly one of `pdf_sha256` or
    `figure_sha256`. It is approved only by a STATE.md line
    `waiver <id>: <reason> (approved by <identity>, <YYYY-MM-DD>)` with the same
    id, reason and explicitly selected approver identity."""
    approvals = {(m.group(1), m.group(2).strip())
                 for m in map(APPROVAL_RE.match, state.splitlines()) if m and m.group(3).strip() == approver}
    usable, invalid, unapproved = [], [], []
    try:
        entries = json.loads(data) if data is not None else []
    except (ValueError, UnicodeError):
        return [], [{"problem": "waivers must be a JSON array"}], []
    if not isinstance(entries, list):
        return [], [{"problem": "waivers must be a JSON array"}], []
    for item in entries:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip()
                                                 for k in WAIVER_KEYS):
            invalid.append({"waiver": item, "problem": "needs " + ", ".join(WAIVER_KEYS)})
        elif ("pdf_sha256" in item) == ("figure_sha256" in item):
            invalid.append({"waiver": item, "problem": "needs exactly one of pdf_sha256 or figure_sha256"})
        elif not approver or item["approved_by"] != approver or (item["id"], item["reason"].strip()) not in approvals:
            unapproved.append({"waiver": item, "problem": "approved_by and STATE.md approval must match "
                                                        "the explicit --approver identity, id and reason"})
        else:
            usable.append(item)
    return usable, invalid, unapproved


def read_bound(path):
    """(bytes, file record) read once, so the bound hash describes the bytes used."""
    if path is None or not path.is_file():
        return None, None
    data = path.read_bytes()
    return data, {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def coverage_report(contract, inputs):
    """Require an explicit disposition for each optional mechanical check.

    External evidence is hash-bound and PDF-specific, not independently certified
    by this function. Its scope and adequacy remain the owner's responsibility.
    """
    supplied = {"build": bool(inputs["log"]), "bibliography": bool(inputs["blg"]),
                "numbers": bool(inputs["values"]), "inventory": bool(inputs["pagemap"]),
                "plan": bool(inputs["plan"]), "reuse": bool(inputs["previous_manifest"])}
    checks, evidence = {}, []
    declarations = contract.get("checks", {}) if isinstance(contract, dict) else {}
    if not isinstance(declarations, dict):
        declarations = {}
    for name, ran in supplied.items():
        declaration = declarations.get(name, {})
        disposition = declaration.get("status") if isinstance(declaration, dict) else None
        reason = declaration.get("reason", "") if isinstance(declaration, dict) else ""
        status = "passed" if ran else "not_assessed"
        if not ran and disposition == "not_applicable" and isinstance(reason, str) and reason.strip():
            status = "not_applicable"
        elif not ran and disposition == "external" and isinstance(reason, str) and reason.strip():
            raw_path = declaration.get("path")
            path = Path(raw_path) if isinstance(raw_path, str) else Path()
            if (path.is_absolute() and path.is_file() and declaration.get("pdf_sha256") == inputs["pdf"]["sha256"]
                    and sha256_file(path) == declaration.get("sha256")):
                evidence.append(file_record(path))
                status = "external"
        checks[name] = {"status": status, "reason": reason}
    complete = all(item["status"] != "not_assessed" for item in checks.values())
    return {"complete": complete, "checks": checks,
            "note": "External evidence and applicability reasons require owner review; no semantic certification."}, evidence


def review_preflight(args):
    """Validate a bounded visual dispatch request; never launch a model."""
    try:
        record = json.loads(args.gate.read_text())
        request = json.loads(args.request.read_text())
        if not isinstance(record, dict) or not isinstance(request, dict):
            raise ValueError("gate and request must be JSON objects")
    except (OSError, ValueError) as error:
        emit({"command": "review-preflight", "ready": False, "errors": [str(error)]}, args.json)
        return 1
    def text(value):
        return isinstance(value, str) and bool(value.strip())

    errors = []
    if request.get("gate_sha256") != sha256_file(args.gate):
        errors.append("request must bind this gate.json by gate_sha256")
    if record.get("blocked") is not False or not record.get("coverage", {}).get("complete"):
        errors.append("mechanical failures or incomplete applicability coverage block dispatch")
    # Recheck gate inputs and outputs, including external checks and PNG bytes.
    def bindings(value):
        if isinstance(value, dict):
            if "path" in value and "sha256" in value:
                yield value
            for child in value.values():
                yield from bindings(child)
        elif isinstance(value, list):
            for child in value:
                yield from bindings(child)
    for binding in bindings({"inputs": record.get("inputs"), "outputs": record.get("outputs")}):
        path = Path(binding["path"])
        # Ordinary coordination can change; applied waiver approval evidence cannot.
        if binding == record.get("inputs", {}).get("state") and not record.get("waivers", {}).get("applied"):
            continue
        if not path.is_file() or sha256_file(path) != binding["sha256"]:
            errors.append(f"stale binding: {path}")
    packet = record.get("outputs", {}).get("packet")
    manifest = json.loads(Path(packet["path"]).read_text()) if packet else {}
    if packet:
        problem = manifest_problem(Path(packet["path"]), manifest)
        if problem:
            errors.append(problem)
        if manifest.get("sha256") != record.get("inputs", {}).get("pdf", {}).get("sha256"):
            errors.append("packet belongs to another PDF")
        for sheet in manifest.get("contact_sheets", []):
            path = Path(packet["path"]).parent / sheet["png"]
            if not path.is_file() or sha256_file(path) != sheet["png_sha256"]:
                errors.append(f"stale contact sheet: {path}")
    count = manifest.get("page_count", 0)
    selected = request.get("pages", [])
    if (not isinstance(selected, list) or not selected or
            any(type(p) is not int or not 1 <= p <= count for p in selected) or
            len(set(selected)) != len(selected)):
        errors.append("pages must be a nonempty unique list of valid page numbers")
        selected = []
    for name in ("model", "effort", "route_reason", "reading_tasks", "stop_condition"):
        if not text(request.get(name)):
            errors.append(f"missing {name}")
    tier = request.get("cost_tier")
    if tier not in ("economy", "escalated"):
        errors.append("cost_tier must be economy or escalated")
    if (args.escalated_models and tier != "escalated" and
            re.search(args.escalated_models, str(request.get("model", "")), re.I)):
        errors.append(f"model matches --escalated-models {args.escalated_models!r}; "
                      "label it escalated with a reason")
    if tier == "escalated" and not text(request.get("escalation_reason")):
        errors.append("expensive visual review needs a concrete unresolved capability/finding")
    if len(selected) > 12 and not text(request.get("scope_reason")):
        errors.append("review of more than 12 pages needs scope_reason beyond final status or pagination")
    # Each candidate is selected or assigned to a justified family whose sample
    # is actually selected. This records sampling, not a fictitious all-page GO.
    candidates = set(record.get("review_pages", []))
    accounted = set(selected)
    families = request.get("families", [])
    if not isinstance(families, list):
        errors.append("families must be a list")
        families = []
    for family in families:
        if not isinstance(family, dict):
            errors.append("each family must be an object")
            continue
        members, samples = family.get("pages", []), family.get("samples", [])
        if (not isinstance(members, list) or not isinstance(samples, list) or
                not members or not samples or not text(family.get("reason")) or
                any(type(p) is not int or not 1 <= p <= count for p in members + samples) or
                not set(samples) <= set(members) or not set(samples) <= set(selected)):
            errors.append("family needs valid members, selected samples and a reuse/sampling reason")
        elif candidates.intersection(members) and not candidates.intersection(samples):
            errors.append("a family with review candidates must sample a candidate page")
        else:
            accounted.update(members)
    if candidates - accounted:
        errors.append(f"candidate pages lack selection or family disposition: {sorted(candidates - accounted)}")
    result = {"command": "review-preflight", "ready": not errors, "errors": errors,
              "gate_sha256": sha256_file(args.gate), "request_sha256": sha256_file(args.request),
              "model": request.get("model"), "pages": selected,
              "note": "Validated request only; not a model launch, visual verdict or semantic approval."}
    emit(result, args.json)
    return 1 if errors else 0


def gate(args):
    session, out = args.session.resolve(strict=True), args.out
    if out.exists():
        raise SystemExit(f"refusing to overwrite the existing gate output {out}")
    if (args.previous_manifest is None) != (args.reviewed is None):
        raise SystemExit("--previous-manifest and --reviewed go together")
    if args.plan and not args.pagemap:
        raise SystemExit("--plan needs --pagemap")
    if args.approver is not None and not re.fullmatch(r"[^,()\r\n]+", args.approver):
        raise SystemExit("--approver must be a nonempty single-line identity without commas or parentheses")
    if args.approver is not None and args.approver != args.approver.strip():
        raise SystemExit("--approver must not have surrounding whitespace")
    if (session / "waivers.json").exists() and not args.approver:
        raise SystemExit("--approver is required when waivers.json exists")
    # Bind every input before any check reads it; verify the bindings again at the end.
    inputs = {name: file_record(path) for name, path in (
        ("pdf", args.pdf), ("log", args.log), ("blg", args.blg), ("values", args.values),
        ("pagemap", args.pagemap), ("plan", args.plan), ("previous_manifest", args.previous_manifest),
        ("reviewed", args.reviewed), ("contract", args.contract), ("blank_exceptions", args.blank_exceptions))}
    waiver_data, inputs["waivers"] = read_bound(session / "waivers.json")
    state_data, inputs["state"] = read_bound(session / "STATE.md")
    lint_argv = ["lint-pdf", str(args.pdf), "--max-blank-band", str(args.max_blank_band), "--profile", args.profile]
    for flag, value in (("--log", args.log), ("--blg", args.blg), ("--blank-exceptions", args.blank_exceptions)):
        if value:
            lint_argv += [flag, str(value)]
    report = lint_report(parser().parse_args(lint_argv))
    out.mkdir(parents=True)
    (out / "lint.json").write_text(json.dumps(report, indent=2) + "\n")
    manifest = build_packet(args.pdf, out / "packet", args.dpi, args.sheet)
    findings = list(report["findings"])
    outcomes = {"build": not any(f["severity"] == "fail" and f["check"].startswith("log-")
                                  for f in findings),
                "bibliography": not any(f["severity"] == "fail" and f["check"].startswith("blg-")
                                         for f in findings)}
    inputs["sources"] = []
    observed = [("lint", report["sha256"]), ("packet", manifest["sha256"])]
    for name, given, build in (("numbers", args.values, lambda: numbers_report(args.pdf, args.values)),
                               ("inventory", args.pagemap,
                                lambda: inventory_report(args.pdf, args.pagemap, args.plan))):
        if given:
            extra = build()
            (out / f"{name}.json").write_text(json.dumps(extra, indent=2) + "\n")
            findings += extra["findings"]
            outcomes[name] = not any(f["severity"] == "fail" for f in extra["findings"])
            if name == "inventory":
                outcomes["plan"] = outcomes[name]
            if name == "numbers":
                inputs["sources"] = extra["sources"]
            observed.append((name, extra["sha256"]))
    comparison = None
    if args.previous_manifest:
        try:
            comparison = diff_report(args.previous_manifest, out / "packet" / "manifest.json", args.reviewed)
            (out / "diff.json").write_text(json.dumps(comparison, indent=2) + "\n")
            outcomes["reuse"] = True
        except Refused as error:
            comparison = {"refused": str(error)}
            outcomes["reuse"] = False
            findings.append(finding("diff-refused", "fail", f"carry-over refused: {error}"))
    inputs["figures"] = [{**figure, "sidecar": None if figure["sidecar_sha256"] is None else {
        "path": str(Path(figure["path"]).with_suffix(".figcheck.json")), "sha256": figure["sidecar_sha256"]}}
        for figure in report["figures"]]
    contract = json.loads(args.contract.read_text()) if args.contract else None
    coverage, inputs["external_checks"] = coverage_report(contract, inputs)
    for name, passed in outcomes.items():
        if coverage["checks"][name]["status"] == "passed" and not passed:
            coverage["checks"][name]["status"] = "failed"
    for step, digest in observed:
        if digest != inputs["pdf"]["sha256"]:
            findings.append(finding("input-changed", "fail", f"{step} read a PDF with sha256 {digest}, "
                                    f"not the bound {inputs['pdf']['sha256']}", value=step))
    bound = [record for name, record in inputs.items() if name not in ("figures", "sources", "external_checks") and record]
    bound += inputs["sources"] + inputs["figures"] + inputs["external_checks"]
    bound += [figure["sidecar"] for figure in inputs["figures"] if figure["sidecar"]]
    for record in bound:
        path = Path(record["path"])
        try:
            unchanged = path.is_file() and sha256_file(path) == record["sha256"]
        except OSError:
            unchanged = False
        if not unchanged:
            findings.append(finding("input-changed", "fail", f"{path} changed while the gate ran",
                                    value=str(path)))
    waivers, invalid, unapproved = read_waivers(
        waiver_data, state_data.decode(errors="replace") if state_data else "", args.approver)
    figure_sha = {figure["path"]: figure["sha256"] for figure in inputs["figures"]}
    applied, unmatched, waived = [], [], set()
    for waiver in waivers:
        covered = [i for i, item in enumerate(findings)
                   if item["severity"] == "fail" and item["check"] == waiver["check"]
                   and item["fingerprint"] == waiver["fingerprint"]
                   and ("figure_sha256" in waiver and waiver["figure_sha256"] == figure_sha.get(item["figure"])
                        if item.get("figure") is not None
                        else "pdf_sha256" in waiver and waiver["pdf_sha256"] == inputs["pdf"]["sha256"])]
        if len(covered) == 1:
            waived.add(covered[0])
            applied.append({"waiver": waiver, "finding": findings[covered[0]]})
        else:
            unmatched.append({"waiver": waiver, "matches": len(covered)})
    blocking = [item for i, item in enumerate(findings) if item["severity"] == "fail" and i not in waived]
    by_check = defaultdict(list)
    for item in findings:
        by_check[item["check"]].append(item)
    every_page = [page["page"] for page in manifest["pages"]]
    review_pages = comparison["review_pages"] if comparison and "review_pages" in comparison else every_page
    record = {
        "command": "gate", "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "session": str(session),
        "approver": args.approver,
        "inputs": inputs,
        "outputs": {"lint": file_record(out / "lint.json"), "packet": file_record(out / "packet" / "manifest.json"),
                    **{name: file_record(out / f"{name}.json") if (out / f"{name}.json").exists() else None
                       for name in ("diff", "numbers", "inventory")}},
        "blocked": bool(blocking),
        "coverage": coverage,
        "ready_for_review": not blocking and coverage["complete"],
        "blocking": blocking,
        "waivers": {"applied": applied, "unmatched": unmatched, "unapproved": unapproved, "invalid": invalid},
        "review_pages": review_pages,
        "contact_sheets": [sheet["png"] for sheet in manifest["contact_sheets"]],
        "diff": None if comparison is None else {k: comparison.get(k) for k in ("refused", "carried_pages", "review_pages")},
        "checks": dict(sorted(by_check.items())),
        "note": "blocked reports detected failures, not coverage. ready_for_review also requires "
                "complete applicability. review_pages are candidates; review-preflight validates "
                "a justified bounded selection and explicit model before dispatch.",
    }
    (out / "gate.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"gate": str(out / "gate.json"), "blocked": record["blocked"],
                      "blocking": len(blocking), "review_pages": len(review_pages)}))
    return 1 if blocking else 0


def parser():
    value = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = value.add_subparsers(dest="command", required=True)
    lint = commands.add_parser("lint-pdf", help="mechanical checks on a final PDF")
    lint.add_argument("pdf", type=Path)
    lint.add_argument("--log", type=Path, help="LaTeX log; also lists included figure PDFs")
    lint.add_argument("--blg", type=Path, help="Biber log")
    lint.add_argument("--figure", type=Path, action="append",
                      help="figure PDF to check (replaces the figures found in the PDF and log)")
    lint.add_argument("--no-figure-check", action="store_true",
                      help="skip figure checks; recorded as an info finding")
    lint.add_argument("--min-font-pt", type=float, default=5.0,
                      help="blocking floor in TeX pt (fail; default 5)")
    lint.add_argument("--flag-font-pt", type=float, default=7.0,
                      help="advisory size in TeX pt (flag; default 7, 6.97 PDF pt passes)")
    lint.add_argument("--max-blank-band", type=float, default=BLANK_BAND_MAX,
                      help="largest blank band allowed, as a fraction of the page height (default %(default)s)")
    lint.add_argument("--blank-exceptions", type=Path,
                      help="JSON list of {raster_sha256, reason}: recorded pages excepted from page-blank-band")
    lint.add_argument("--profile", choices=("report", "slides"), default="report",
                      help="slides: frame-aware off-page text, figure font flags, no blank-band or density checks")
    lint.add_argument("--json", type=Path, help="write the report here instead of stdout")
    pack = commands.add_parser("packet", help="page PNGs, contact sheets and manifest")
    pack.add_argument("pdf", type=Path)
    pack.add_argument("--out", type=Path, required=True)
    pack.add_argument("--dpi", type=int, default=120)
    pack.add_argument("--sheet", default="4x3", help="contact sheet tiles, COLUMNSxROWS")
    pack.add_argument("--force", action="store_true", help="replace an existing packet in --out")
    compare = commands.add_parser("diff", help="which page verdicts carry over")
    compare.add_argument("old", type=Path)
    compare.add_argument("new", type=Path)
    compare.add_argument("--reviewed", type=Path, required=True)
    compare.add_argument("--json", type=Path)
    values = commands.add_parser("numbers", help="find every printed value of an analyb manifest in the PDF")
    values.add_argument("pdf", type=Path)
    values.add_argument("manifest", type=Path, help="analyb.printed_values JSON")
    values.add_argument("--json", type=Path)
    pages = commands.add_parser("inventory", help="compare the PDF with an analyb plotbook page map")
    pages.add_argument("pdf", type=Path)
    pages.add_argument("pagemap", type=Path, help="analyb.plotbook_page_map JSON")
    pages.add_argument("--plan", type=Path, help="JSON list of required {figure | key, group}")
    pages.add_argument("--json", type=Path)
    run = commands.add_parser("gate", help="bind inputs, run lint-pdf, packet and diff, write gate.json")
    run.add_argument("--session", type=Path, required=True, help="session directory (holds waivers.json)")
    run.add_argument("--approver", help="approval identity; required when session/waivers.json exists")
    run.add_argument("--pdf", type=Path, required=True)
    run.add_argument("--log", type=Path)
    run.add_argument("--blg", type=Path)
    run.add_argument("--previous-manifest", type=Path, help="packet manifest of the last reviewed version")
    run.add_argument("--reviewed", type=Path, help="reviewed raster hashes for --previous-manifest")
    run.add_argument("--values", type=Path, help="analyb printed-value manifest for numbers")
    run.add_argument("--pagemap", type=Path, help="analyb plotbook page map for inventory")
    run.add_argument("--plan", type=Path, help="coverage plan for inventory")
    run.add_argument("--contract", type=Path, help="JSON applicability dispositions for absent checks")
    run.add_argument("--max-blank-band", type=float, default=BLANK_BAND_MAX, help="passed to lint-pdf")
    run.add_argument("--blank-exceptions", type=Path, help="passed to lint-pdf; bound by hash")
    run.add_argument("--profile", choices=("report", "slides"), default="report", help="passed to lint-pdf")
    run.add_argument("--dpi", type=int, default=120)
    run.add_argument("--sheet", default="4x3")
    run.add_argument("--out", type=Path, required=True, help="new directory for gate.json and its outputs")
    preflight = commands.add_parser("review-preflight", help="validate visual scope, route and mechanical readiness")
    preflight.add_argument("--escalated-models", help="regex of models that are never an economy route, e.g. 'opus|astra'")
    preflight.add_argument("--gate", type=Path, required=True)
    preflight.add_argument("--request", type=Path, required=True)
    preflight.add_argument("--json", type=Path)
    return value


def main(argv=None):
    args = parser().parse_args(argv)
    return {"lint-pdf": lint_pdf, "packet": packet, "diff": diff, "numbers": numbers,
            "inventory": inventory, "gate": gate, "review-preflight": review_preflight}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
