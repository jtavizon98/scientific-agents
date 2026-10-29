import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "skills" / "render-review" / "scripts" / "render_gate.py"
SPEC = importlib.util.spec_from_file_location("render_gate", MODULE_PATH)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
except ImportError:  # pragma: no cover - depends on host
    plt = None
try:
    from PIL import Image
except ImportError:  # pragma: no cover - depends on host
    Image = None


def needs(*tools):
    absent = [t for t in tools if (plt is None if t == "matplotlib" else shutil.which(t) is None)]
    return unittest.skipIf(absent, "missing " + ", ".join(absent))


def figure(path, draw, fonttype=42, size=(4, 3), **save):
    """Save a matplotlib figure with default style and embedded TrueType fonts."""
    with matplotlib.rc_context(matplotlib.rcParamsDefault):
        matplotlib.rcParams["pdf.fonttype"] = fonttype
        fig = plt.figure(figsize=size)
        draw(fig)
        fig.savefig(path, **save)
        plt.close(fig)
    return path


def latex(folder, body, preamble="", *options):
    source = Path(folder) / "doc.tex"
    source.write_text("\\documentclass[10pt]{article}\n\\usepackage[T1]{fontenc}\n\\usepackage{lmodern}\n"
                      "\\usepackage{graphicx}\n" + preamble + "\n\\begin{document}\n" + body + "\n\\end{document}\n")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", *options, source.name], cwd=folder,
                   capture_output=True, text=True)
    return source.with_suffix(".pdf"), source.with_suffix(".log")


RAW_PDF_JS = """var doc = new PDFDocument();
var font = doc.addSimpleFont(new Font("Times-Roman"), "Latin");
var page = doc.addPage([0, 0, 612, 792], 0, doc.addObject({Font: {F1: font}}), scriptArgs[1]);
doc.insertPage(-1, page);
doc.save(scriptArgs[0]);
"""


def raw_pdf(path, content):
    """One-page PDF with the given content stream; /F1 is Times-Roman (not embedded)."""
    script = path.with_suffix(".js")
    script.write_text(RAW_PDF_JS)
    subprocess.run(["mutool", "run", str(script), str(path), content], check=True, capture_output=True)
    return path


REPLACE_CONTENT_JS = """var doc = Document.openDocument(scriptArgs[0]);
doc.loadPage(0).getObject().put("Contents", doc.addStream(scriptArgs[2], {}));
doc.save(scriptArgs[1]);
"""


def replace_content(source, target, content):
    """Copy of `source` (keeping its resources) with a new page content stream."""
    script = target.with_suffix(".js")
    script.write_text(REPLACE_CONTENT_JS)
    subprocess.run(["mutool", "run", str(script), str(source), str(target), content], check=True, capture_output=True)
    return target


DENSITY_CHECKS = {"panel-narrow", "page-underused"}


def lint(*argv, density=False):
    """Run lint-pdf; advisory density flags are dropped unless `density`."""
    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder) / "report.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["lint-pdf", *map(str, argv), "--json", str(out)])
        report = json.loads(out.read_text())
    if not density:
        report["findings"] = [f for f in report["findings"] if f["check"] not in DENSITY_CHECKS]
    return code, report


def checks(report, severity=None):
    return [f["check"] for f in report["findings"] if severity is None or f["severity"] == severity]


def clipped_figure(fig):
    ax = fig.add_axes([0.15, 0.2, 0.85, 0.6])  # right spine on the canvas edge
    ax.plot([0, 1000], [0, 1], label="first series")
    ax.plot([0, 1000], [1, 0], label="second series")
    ax.set_xlim(0, 1000)
    ax.set_xticks([0, 500, 1000])
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.3), ncol=2)  # top row above the canvas


@needs("mutool", "pdflatex", "pdffonts", "matplotlib")
class LintPdfTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)

    def test_clean_document_has_no_fail(self):
        figure(self.folder / "fig.pdf", lambda f: f.add_subplot().plot([0, 1], [0, 1]), bbox_inches="tight")
        pdf, log = latex(self.folder, "Body text with $x_i^2 + \\int_0^1 f$ and kerning AVAWAY.\n\n"
                         "\\noindent\\includegraphics[width=\\linewidth]{fig.pdf}")
        code, report = lint(pdf, "--log", log)
        self.assertEqual(checks(report, "fail"), [])
        self.assertEqual(code, 0)
        self.assertEqual(len(report["figures"]), 1)
        self.assertEqual(report["figures"][0]["used_on_pages"], [1])
        # Limits or indices that structured text splits from their base count as ordinary 7 pt text.
        self.assertGreaterEqual(report["page_fonts"][0]["min_base_pt"], 6.95)

    def test_font_size_is_measured_at_final_scale(self):
        figure(self.folder / "fig.pdf", lambda f: f.text(0.1, 0.5, "Eight point label", fontsize=8))
        pdf, _ = latex(self.folder, "\\includegraphics[width=288bp]{fig.pdf}\n\n"
                       "\\includegraphics[width=144bp]{fig.pdf}")
        code, report = lint(pdf)
        below = [f for f in report["findings"] if f["check"] == "font-below-floor"]
        self.assertEqual(code, 1)
        self.assertEqual(len(below), 1)
        self.assertAlmostEqual(below[0]["value"], 4.0, places=1)
        self.assertIn("Eight point label", below[0]["message"])
        soft = [f for f in report["findings"] if f["check"] == "font-below-advisory"]
        self.assertEqual(soft, [])  # 8 pt at full size passes; the 4 pt copy fails once, not twice

    def test_scripts_are_exempt_from_floor_but_flagged_below_five(self):
        body = ("Normal $x_i^2$ uses 7 pt scripts.\n\n"
                "{\\fontsize{12}{14}\\selectfont Base $x_{\\mbox{\\fontsize{4}{5}\\selectfont q}}$ tiny script.}\n\n"
                "{\\fontsize{4}{5}\\selectfont Four point line.}")
        pdf, _ = latex(self.folder, body)
        _, report = lint(pdf)
        fails = [f for f in report["findings"] if f["severity"] == "fail"]
        flags = [f for f in report["findings"] if f["severity"] == "flag"]
        self.assertEqual([f["check"] for f in fails], ["font-below-floor"] * len(fails))
        self.assertTrue(fails and all("Four point line" in f["message"] for f in fails))
        # The 4 pt script is reported once, as a flag; 7 pt scripts are not advisory findings.
        self.assertEqual([(f["check"], f["severity"]) for f in flags], [("font-below-floor", "flag")])
        self.assertIn("'q'", flags[0]["message"])
        self.assertAlmostEqual(flags[0]["value"], 4.0, places=1)

    def test_floor_is_tex_points_and_advisory_tier_flags(self):
        body = "\n\n".join(f"{{\\fontsize{{{n}}}{{{n + 1}}}\\selectfont Line at {n} TeX pt.}}" for n in (5, 6, 7))
        pdf, _ = latex(self.folder, body)
        code, report = lint(pdf)  # defaults: fail below 5, flag below 7 (TeX pt)
        self.assertEqual(code, 0)
        self.assertEqual([(f["check"], f["severity"], round(f["value"])) for f in report["findings"]],
                         [("font-below-advisory", "flag", 5), ("font-below-advisory", "flag", 6)])
        code, report = lint(pdf, "--min-font-pt", "7", "--flag-font-pt", "9")
        self.assertEqual(code, 1)
        self.assertEqual({round(f["value"]) for f in report["findings"] if f["severity"] == "fail"}, {5, 6})
        self.assertEqual({round(f["value"]) for f in report["findings"] if f["severity"] == "flag"}, {7})

    def test_figures_from_ptex_filename_without_log(self):
        path = figure(self.folder / "fig.pdf", clipped_figure)
        pdf, _ = latex(self.folder, "\\includegraphics[width=0.9\\linewidth]{fig.pdf}")
        _, report = lint(pdf)
        self.assertEqual([f["path"] for f in report["figures"]], [str(path.resolve())])
        self.assertIn("figure-text-clipped", checks(report, "fail"))
        path.unlink()
        code, report = lint(pdf)
        self.assertEqual((code, checks(report, "fail")), (1, ["figure-unresolved"]))
        code, report = lint(pdf, "--no-figure-check")
        self.assertEqual((code, checks(report)), (0, ["figure-check-skipped"]))
        self.assertEqual(report["findings"][0]["severity"], "info")

    def test_script_rule_run_length_and_script_floor(self):
        content = ("BT /F1 12 Tf 1 0 0 1 60 110 Tm (x) Tj /F1 4 Tf 1 0 0 1 66 108.5 Tm (ij) Tj ET "
                   "BT /F1 12 Tf 1 0 0 1 60 200 Tm (y) Tj /F1 3 Tf 1 0 0 1 66 198.5 Tm (k) Tj ET "
                   "BT /F1 12 Tf 1 0 0 1 60 300 Tm (z) Tj /F1 4 Tf 1 0 0 1 66 298.5 Tm (abcd) Tj ET")
        _, report = lint(raw_pdf(self.folder / "scripts.pdf", content))
        found = sorted((f["severity"], f["message"].split(": ")[1].split(" in ")[0])
                       for f in report["findings"] if f["check"] == "font-below-floor")
        # 4 pt "ij" is a script (flag); 3 pt "k" is below the 3.5 pt script floor; "abcd" is too long.
        self.assertEqual(found, [("fail", "'abcd'"), ("fail", "'k'"), ("flag", "'ij'")])

    def test_same_text_object_small_label_is_not_a_script(self):
        # Review input: one BT...ET places 12 pt "A" and ordinary 4 pt "small label" beside it.
        content = "BT /F1 12 Tf 1 0 0 1 60 110 Tm (A) Tj /F1 4 Tf 1 0 0 1 69 108.5 Tm (small label) Tj ET"
        code, report = lint(raw_pdf(self.folder / "label.pdf", content))
        fails = [f for f in report["findings"] if f["check"] == "font-below-floor"]
        self.assertEqual((code, [f["severity"] for f in fails]), (1, ["fail"]))
        self.assertIn("small", fails[0]["message"])

    def test_paint_records_are_matched_by_glyph_and_order(self):
        # Review inputs: a clipped-away "A" and a visible "W" share an origin, then "X" overlaps "W";
        # an invisible 3 pt "hidden" shares the origin of a visible "X".
        clips = ("q 0 200 612 100 re W n BT /F1 20 Tf 1 0 0 1 60 110 Tm (A) Tj ET Q "
                 "BT /F1 20 Tf 1 0 0 1 60 110 Tm (W) Tj ET BT /F1 20 Tf 1 0 0 1 60 105 Tm (X) Tj ET")
        _, report = lint(raw_pdf(self.folder / "clips.pdf", clips))
        self.assertEqual([f["message"] for f in report["findings"] if f["check"] == "text-overlap"],
                         ["'W' overlaps 'X' (1 glyph intersections)"])
        hidden = "BT /F1 12 Tf 1 0 0 1 60 110 Tm (X) Tj ET BT 3 Tr /F1 3 Tf 1 0 0 1 60 110 Tm (hidden) Tj ET"
        _, report = lint(raw_pdf(self.folder / "hidden.pdf", hidden))
        self.assertEqual(checks(report), ["font-not-embedded"])
        self.assertEqual(report["extraction"]["invisible_glyphs"], 6)
        # The same character at the same origin, once visible and once invisible: ambiguous.
        twin = "BT /F1 12 Tf 1 0 0 1 60 110 Tm (X) Tj ET BT 3 Tr /F1 12 Tf 1 0 0 1 60 110 Tm (X) Tj ET"
        _, report = lint(raw_pdf(self.folder / "twin.pdf", twin))
        self.assertIn("extraction-ambiguous", checks(report, "info"))
        self.assertEqual(report["extraction"]["ambiguous_glyphs"], 1)

    def test_visible_type3_text_is_checked(self):
        def draw(fig):  # review input, saved with pdf.fonttype 3
            fig.text(.95, .5, "tiny label", fontsize=3)
            fig.text(.2, .3, "AAAAA", fontsize=20)
            fig.text(.21, .31, "BBBBB", fontsize=20)
        code, report = lint(figure(self.folder / "t3.pdf", draw, fonttype=3))
        self.assertEqual(code, 1)
        self.assertEqual(report["extraction"]["invisible_glyphs"], 0)
        self.assertTrue({"font-below-floor", "text-overlap"} <= set(checks(report, "fail")))

    def test_script_run_needs_the_base_text_object_for_every_glyph(self):
        # Review inputs: "j" from another text object, or with an ambiguous paint record.
        cross = ("BT /F1 12 Tf 1 0 0 1 60 110 Tm (A) Tj /F1 4 Tf 1 0 0 1 69 108.5 Tm (i) Tj ET "
                 "BT /F1 4 Tf 1 0 0 1 70.112 108.5 Tm (j) Tj ET")
        ambiguous = ("BT /F1 12 Tf 1 0 0 1 60 110 Tm (A) Tj /F1 4 Tf 1 0 0 1 69 108.5 Tm (ij) Tj ET "
                     "BT 3 Tr /F1 4 Tf 1 0 0 1 70.112 108.5 Tm (j) Tj ET")
        for name, content in (("cross", cross), ("ambiguous", ambiguous)):
            with self.subTest(name):
                code, report = lint(raw_pdf(self.folder / f"{name}.pdf", content))
                floor = [(f["severity"], f["value"]) for f in report["findings"] if f["check"] == "font-below-floor"]
                self.assertEqual((code, floor), (1, [("fail", 4.0)]))

    def test_type3_visibility_needs_its_own_glyph_procedure(self):
        hidden = figure(self.folder / "alpha.pdf", lambda f: f.text(0.3, 0.5, "transparent", fontsize=3, alpha=0),
                        fonttype=3)
        code, report = lint(hidden)
        self.assertEqual((code, checks(report, "fail")), (0, []))
        self.assertEqual(report["extraction"]["invisible_glyphs"], 11)
        # Review input: an unrelated rectangle painted before invisible (mode 3) Type 3 text.
        base = figure(self.folder / "t3.pdf", lambda f: f.text(0.3, 0.5, "X", fontsize=12), fonttype=3)
        after_rect = replace_content(base, self.folder / "rect.pdf",
                                     "0 0 0 rg 10 10 10 10 re f BT 3 Tr /F1 3 Tf 1 0 0 1 60 110 Tm (X) Tj ET")
        code, report = lint(after_rect)
        self.assertEqual((code, report["extraction"]["invisible_glyphs"]), (0, 1))
        visible = replace_content(base, self.folder / "shown.pdf",
                                  "0 0 0 rg 10 10 10 10 re f BT /F1 3 Tf 1 0 0 1 60 110 Tm (X) Tj ET")
        code, report = lint(visible)
        self.assertEqual((code, checks(report, "fail")), (1, ["font-below-floor"]))

    def test_coincident_page_path_cannot_paint_an_invisible_type3_glyph(self):
        base = figure(self.folder / "t3-coincident.pdf", lambda f: f.text(.3, .5, "X", fontsize=12), fonttype=3)
        rectangle = "q 1 0 0 1 60 110 cm 0 0 0 rg 0 0 10 10 re f Q "
        control = replace_content(base, self.folder / "control.pdf", rectangle)
        hidden = replace_content(base, self.folder / "hidden-coincident.pdf", rectangle +
                                 "BT 3 Tr /F1 3 Tf 1 0 0 1 60 110 Tm (X) Tj ET")
        for pdf in (control, hidden):
            subprocess.run(["mutool", "draw", "-o", str(pdf.with_suffix(".png")), str(pdf)],
                           check=True, capture_output=True)
        self.assertEqual(gate.raster_sha256(control.with_suffix(".png")),
                         gate.raster_sha256(hidden.with_suffix(".png")))
        code, report = lint(hidden)
        self.assertEqual((code, checks(report, "fail"), report["extraction"]["invisible_glyphs"]), (0, [], 1))
        shown = replace_content(base, self.folder / "shown-coincident.pdf", rectangle +
                                "BT /F1 3 Tf 1 0 0 1 60 110 Tm (X) Tj ET")
        code, report = lint(shown)
        self.assertEqual((code, checks(report, "fail"), report["extraction"]["invisible_glyphs"]),
                         (1, ["font-below-floor"], 0))

    def test_blank_type3_procedure_is_invisible_on_every_text_callback_route(self):
        base = figure(self.folder / "t3-procedure.pdf", lambda f: f.text(.3, .5, "Y", fontsize=12), fonttype=3)
        script = self.folder / "blank-procedure.js"
        script.write_text('var doc = Document.openDocument(scriptArgs[0]);\n'
                          'var page = doc.loadPage(0).getObject();\n'
                          'var proc = page.getInheritable("Resources").get("Font").get("F1").get("CharProcs").get("Y");\n'
                          'proc.writeStream("611 0 -2 0 613 730 d1\\n");\n'
                          'page.put("Contents", doc.addStream(scriptArgs[2], {}));\n'
                          'doc.save(scriptArgs[1]);\n')
        control = replace_content(base, self.folder / "blank-page.pdf", "")
        subprocess.run(["mutool", "draw", "-o", str(control.with_suffix(".png")), str(control)],
                       check=True, capture_output=True)
        empty_raster = gate.raster_sha256(control.with_suffix(".png"))
        for mode in (0, 1, 2):  # fill, stroke, and fill/stroke: blank Type 3 text can use direct callbacks
            with self.subTest(render_mode=mode):
                content = f"BT {mode} Tr /F1 3 Tf 1 0 0 1 60 110 Tm (Y) Tj ET"
                blank = self.folder / f"blank-procedure-{mode}.pdf"
                subprocess.run(["mutool", "run", str(script), str(base), str(blank), content],
                               check=True, capture_output=True)
                painted = replace_content(base, self.folder / f"painted-procedure-{mode}.pdf", content)
                for pdf in (blank, painted):
                    subprocess.run(["mutool", "draw", "-o", str(pdf.with_suffix(".png")), str(pdf)],
                                   check=True, capture_output=True)
                self.assertEqual(gate.raster_sha256(blank.with_suffix(".png")), empty_raster)
                self.assertNotEqual(gate.raster_sha256(painted.with_suffix(".png")), empty_raster)
                code, report = lint(blank)
                self.assertEqual((code, checks(report, "fail"), report["extraction"]),
                                 (0, [], {"invisible_glyphs": 1, "unmatched_glyphs": 0, "ambiguous_glyphs": 0}))
                code, report = lint(painted)
                self.assertEqual((code, checks(report, "fail"), report["extraction"]["invisible_glyphs"]),
                                 (1, ["font-below-floor"], 0))

    def test_ligature_parts_share_their_paint_record(self):
        # Review input: invisible 4 pt "fi fl" in render mode 3 with an embedded font.
        hidden, _ = latex(self.folder, "\\pagestyle{empty}\\pdfliteral direct{3 Tr}"
                          "{\\fontsize{4}{5}\\selectfont fi fl}\\pdfliteral direct{0 Tr}")
        code, report = lint(hidden)
        self.assertEqual((code, report["findings"]), (0, []))
        self.assertEqual((report["extraction"]["invisible_glyphs"], report["extraction"]["unmatched_glyphs"]), (4, 0))
        shown, _ = latex(self.folder, "\\pagestyle{empty}{\\fontsize{4}{5}\\selectfont fi fl}")
        code, report = lint(shown)
        self.assertEqual((code, report["extraction"]["unmatched_glyphs"]), (1, 0))
        self.assertIn("'fi fl'", report["findings"][0]["message"])

    def test_separate_small_label_beside_large_text_is_not_a_script(self):
        def draw(fig):  # review input: a 4 pt label placed beside a 12 pt "A"
            fig.text(0.3, 0.5, "A", fontsize=12)
            fig.text(0.333, 0.49, "small label", fontsize=4)
        code, report = lint(figure(self.folder / "fig.pdf", draw))
        fails = [f for f in report["findings"] if f["severity"] == "fail"]
        self.assertEqual(code, 1)
        self.assertEqual([f["check"] for f in fails], ["font-below-floor"])
        self.assertIn("small label", fails[0]["message"])

    def test_invisible_text_is_ignored(self):
        body = ("Visible line.\\par\\noindent\\hspace*{-4cm}\\pdfliteral direct{3 Tr}"
                "{\\fontsize{3}{4}\\selectfont Invisible tiny text}\\pdfliteral direct{0 Tr}\\par")
        pdf, _ = latex(self.folder, body)
        code, report = lint(pdf)
        self.assertEqual((code, report["findings"]), (0, []))
        self.assertGreater(report["extraction"]["invisible_glyphs"], 10)
        transparent = figure(self.folder / "alpha.pdf", lambda f: f.text(0.95, 0.5, "Transparent", fontsize=3, alpha=0))
        code, report = lint(transparent)
        self.assertEqual((code, report["findings"]), (0, []))

    def test_user_unit_scales_extraction_offset(self):
        clean = figure(self.folder / "clean.pdf", lambda f: f.text(0.2, 0.5, "Clean label", fontsize=12))
        scaled = self.folder / "userunit.pdf"
        script = self.folder / "userunit.js"
        script.write_text("var doc = Document.openDocument(scriptArgs[0]);\n"
                          "doc.loadPage(0).getObject().put('UserUnit', 2);\ndoc.save(scriptArgs[1]);\n")
        subprocess.run(["mutool", "run", str(script), str(clean), str(scaled)], check=True, capture_output=True)
        code, report = lint(scaled)
        self.assertEqual((code, report["findings"]), (0, []))
        self.assertAlmostEqual(report["page_fonts"][0]["min_base_pt"], 24.0, places=0)

    def test_visible_overlap_with_partly_clipped_word_fails(self):
        # Review input: two words visibly overlap; one is partly clipped by its figure box.
        figure(self.folder / "fig.pdf", lambda f: f.text(0.1, 0.02, "Clipped typography", fontsize=14),
               size=(3, 1))
        body = ("\\setlength{\\unitlength}{1bp}\\noindent\\begin{picture}(216,72)"
                "\\put(0,0){\\includegraphics{fig.pdf}}"
                "\\put(24,3){\\fontsize{14}{14}\\selectfont Overlap}\\end{picture}")
        pdf, _ = latex(self.folder, body)
        code, report = lint(pdf, "--no-figure-check")
        overlaps = [f for f in report["findings"] if f["check"] == "text-overlap"]
        self.assertEqual(code, 1)
        self.assertEqual(len(overlaps), 1)
        self.assertTrue(overlaps[0]["clipped"])

    def test_overlapping_text(self):
        def draw(fig):
            fig.text(0.2, 0.5, "Overlapping label", fontsize=12)
            fig.text(0.23, 0.51, "Another label", fontsize=12)
            fig.text(0.2, 0.2, "Separate line", fontsize=12)
        _, report = lint(figure(self.folder / "fig.pdf", draw))
        overlaps = [f for f in report["findings"] if f["check"] == "text-overlap"]
        self.assertEqual(len(overlaps), 1)
        self.assertIn("Overlapping label", overlaps[0]["message"])
        self.assertIn("Another label", overlaps[0]["message"])
        self.assertEqual(overlaps[0]["page"], 1)

    def test_text_off_page(self):
        def draw(fig):
            fig.text(0.9, 0.5, "Runs off the edge", fontsize=12)
            fig.text(1.2, 0.3, "Wholly outside", fontsize=12)
        _, report = lint(figure(self.folder / "fig.pdf", draw))
        off = [f for f in report["findings"] if f["check"] == "text-off-page"]
        self.assertEqual(len(off), 2)
        self.assertTrue(all("right page edge" in f["message"] for f in off))

    def test_clipped_legend_and_truncated_tick_in_included_figure(self):
        path = figure(self.folder / "fig.pdf", clipped_figure)
        pdf, log = latex(self.folder, "\\includegraphics[width=0.9\\linewidth]{fig.pdf}")
        code, report = lint(pdf, "--log", log)
        clipped = [f for f in report["findings"] if f["check"] == "figure-text-clipped"]
        self.assertEqual(code, 1)
        self.assertTrue(all(f["figure"] == str(path.resolve()) and f["used_on_pages"] == [1] for f in clipped))
        messages = " ".join(f["message"] for f in clipped)
        self.assertIn("'1000' cross the right", messages)
        self.assertIn("'first series' cross the top", messages)
        _, explicit = lint(pdf, "--figure", path)
        self.assertEqual(len([f for f in explicit["findings"] if f["check"] == "figure-text-clipped"]), len(clipped))

    def sidecar(self, path, **changes):
        item = {"check": "legend-outside-axes", "severity": "fail", "where": "axes 0",
                "bbox": [1.74, 1.4516, 2.58, 1.595], "value": 3.0, "message": "legend crosses the spine"}
        record = {"schema": "analyb.figcheck", "schema_version": 1, "pdf": path.name,
                  "pdf_sha256": gate.sha256_file(path), "figure_size_in": [4, 3],
                  "bbox_units": "figure inches from the canvas lower-left corner", "findings": [item]}
        record.update(changes)
        path.with_suffix(".figcheck.json").write_text(json.dumps(record))

    def test_figcheck_sidecar_findings_pass_through_in_their_own_units(self):
        path = figure(self.folder / "fig.pdf", lambda f: f.add_subplot().plot([0, 1]), bbox_inches="tight")
        self.sidecar(path)
        pdf, _ = latex(self.folder, "\\noindent\\includegraphics[width=\\linewidth]{fig.pdf}")
        code, report = lint(pdf)
        passed = [f for f in report["findings"] if f["check"] == "legend-outside-axes"]
        self.assertEqual(code, 1)
        self.assertEqual(passed[0]["figure"], str(path.resolve()))
        self.assertEqual(passed[0]["where"], "axes 0")
        self.assertIsNone(passed[0]["bbox"])
        self.assertEqual(passed[0]["figure_bbox"], [1.74, 1.4516, 2.58, 1.595])
        self.assertIn("inches", passed[0]["figure_bbox_units"])

    def test_stale_or_malformed_sidecar_fails(self):
        path = figure(self.folder / "fig.pdf", lambda f: f.add_subplot().plot([0, 1]), bbox_inches="tight")
        pdf, _ = latex(self.folder, "\\noindent\\includegraphics[width=\\linewidth]{fig.pdf}")
        self.sidecar(path, findings=[])  # review input: clean sidecar, figure overwritten afterwards
        figure(path, lambda f: f.add_subplot().plot([1, 0]), bbox_inches="tight")
        for case in ("stale", "schema", "json"):
            if case == "schema":
                self.sidecar(path, schema_version=99, findings=[])
            if case == "json":
                path.with_suffix(".figcheck.json").write_text("{not json")
            code, report = lint(pdf, "--figure", path)
            stale = [f for f in report["findings"] if f["check"] == "figure-sidecar-stale"]
            self.assertEqual((code, len(stale)), (1, 1), case)
            self.assertEqual(stale[0]["figure"], str(path.resolve()))

    def test_file_line_error_in_log(self):
        pdf, log = latex(self.folder, "\\UnknownCommand Some text.", "", "-file-line-error")
        self.assertTrue(pdf.is_file())
        code, report = lint(pdf, "--log", log)
        self.assertEqual(code, 1)
        self.assertIn("log-error", checks(report, "fail"))
        spaced = self.folder / "doc with space.log"  # review input: a filename with spaces
        spaced.write_text("./doc with space.tex:1: Undefined control sequence.\n")
        self.assertEqual([(f["check"], f["severity"]) for f in gate.check_log(spaced)], [("log-error", "fail")])

    def test_overfull_box_and_undefined_reference_in_log(self):
        pdf, log = latex(self.folder, "See \\ref{missing}.\n\n\\hbox to 20pt{Much wider than twenty points}")
        code, report = lint(pdf, "--log", log)
        found = {f["check"]: f for f in report["findings"] if f.get("source", "").startswith(str(log))}
        self.assertEqual(code, 1)
        self.assertEqual(found["log-overfull"]["severity"], "fail")
        self.assertGreater(found["log-overfull"]["value"], 1)
        self.assertEqual(found["log-undefined-reference"]["severity"], "fail")

    def test_type3_font_is_flagged(self):
        draw = lambda f: f.text(0.1, 0.5, "Type three", fontsize=12)
        _, type3 = lint(figure(self.folder / "t3.pdf", draw, fonttype=3))
        _, truetype = lint(figure(self.folder / "t42.pdf", draw, fonttype=42))
        self.assertIn("font-type3", checks(type3, "flag"))
        self.assertNotIn("font-type3", checks(truetype))


@needs("mutool", "pdflatex", "pdffonts", "matplotlib")
class DensityTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)

    def test_narrow_panel_is_flagged_with_its_final_width(self):
        figure(self.folder / "fig.pdf", lambda f: f.add_subplot().plot([0, 1]), bbox_inches="tight")
        text = "Filler text for a full page. " * 300
        pdf, _ = latex(self.folder, "\\noindent\\includegraphics[width=3cm]{fig.pdf}\\par"
                       "\\noindent\\includegraphics[width=10cm]{fig.pdf}\\par " + text)
        code, report = lint(pdf, density=True)
        narrow = [f for f in report["findings"] if f["check"] == "panel-narrow"]
        self.assertEqual(code, 1)  # the shrunken tick labels fail the font floor; density only flags
        self.assertEqual([(f["severity"], f["page"], round(f["value"], 1)) for f in narrow], [("flag", 1, 3.0)])
        widths = [p["width_cm"] for p in report["density"]["pages"][0]["panels"]]
        self.assertEqual([round(w, 1) for w in widths], [3.0, 10.0])

    def test_underused_page_is_flagged(self):
        # Default article margins: the inferred frame is under half the page, yet full pages pass.
        pdf, _ = latex(self.folder, "Filler text for a full page. " * 900 + "\\newpage Only one line here.")
        code, report = lint(pdf, "--max-blank-band", "1", density=True)  # the last filler page ends early
        pages = report["density"]["pages"]
        self.assertEqual(report["density"]["frame"], "content")
        self.assertGreaterEqual(len(pages), 3)
        self.assertGreater(pages[0]["used_fraction"], 0.5)
        under = [(f["page"], f["severity"]) for f in report["findings"] if f["check"] == "page-underused"]
        self.assertEqual(code, 0)
        self.assertEqual(under, [(len(pages), "flag")])  # only the one-line page

    def test_short_document_uses_the_inset_page_frame(self):
        # Review input: one 72 x 72 pt figure alone on a page reported 100 % use.
        figure(self.folder / "fig.pdf", lambda f: f.add_subplot().plot([0, 1]), size=(1, 1))
        pdf, _ = latex(self.folder, "\\pagestyle{empty}\\noindent\\includegraphics{fig.pdf}")
        _, report = lint(pdf, density=True)
        self.assertEqual(report["density"]["frame"], "page inset by 12 mm")
        self.assertLess(report["density"]["pages"][0]["used_fraction"], 0.05)
        self.assertIn("page-underused", checks(report, "flag"))

    def test_placements_follow_mupdf_not_comments(self):
        # Review input: a comment that looks like a cm operator before the placement.
        figure(self.folder / "fig.pdf", lambda f: f.add_subplot().plot([0, 1]), bbox_inches="tight")
        pdf, _ = latex(self.folder, "\\noindent\\includegraphics[width=7cm]{fig.pdf}")
        commented = self.folder / "commented.pdf"
        script = self.folder / "comment.js"
        script.write_text("var doc = Document.openDocument(scriptArgs[0]);\n"
                          "var c = doc.loadPage(0).getObject().get('Contents');\n"
                          "var text = c.readStream().asString().replace('/Im1 Do', '% 0.1 0 0 0.1 0 0 cm\\n/Im1 Do');\n"
                          "if (text.indexOf('% 0.1') < 0) throw new Error('placement not found');\n"
                          "doc.loadPage(0).getObject().put('Contents', doc.addStream(text, {}));\n"
                          "doc.save(scriptArgs[1]);\n")
        subprocess.run(["mutool", "run", str(script), str(pdf), str(commented)], check=True, capture_output=True)
        for path in (pdf, commented):
            _, report = lint(path, "--no-figure-check", density=True)
            widths = [p["width_cm"] for page in report["density"]["pages"] for p in page["panels"]]
            self.assertEqual([round(w, 1) for w in widths], [7.0], path.name)
            self.assertNotIn("panel-narrow", checks(report))


@needs("mutool", "pdflatex", "pdffonts", "pdftoppm")
class BlankBandTest(unittest.TestCase):
    """Synthetic coverage of large blank bands and raster-bound exceptions."""

    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp())
        # Full page, then a page whose two lines leave most of it blank, then a short last page.
        filler = "Filler text for a full page. " * 130
        cls.pdf, _ = latex(cls.folder, filler + "\\newpage Two short lines.\\par Then nothing."
                           "\\newpage The document ends here.")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder)

    def bands(self, report):
        return [(f["page"], f["severity"]) for f in report["findings"] if f["check"] == "page-blank-band"]

    def test_tall_blank_band_fails_and_final_page_is_only_measured(self):
        code, report = lint(self.pdf, density=True)
        pages = report["density"]["pages"]
        self.assertEqual(len(pages), 3)
        self.assertLess(pages[0]["blank_band"], 0.25)
        self.assertGreater(pages[1]["blank_band"], 0.5)
        self.assertGreater(pages[2]["blank_band"], 0.5)  # measured, but a document may end early
        self.assertEqual((code, self.bands(report)), (1, [(2, "fail")]))
        band = next(f for f in report["findings"] if f["check"] == "page-blank-band")
        self.assertEqual(band["value"], pages[1]["blank_band"])
        self.assertRegex(band["raster_sha256"], "^[0-9a-f]{64}$")
        self.assertLess(band["bbox"][1], band["bbox"][3])
        code, report = lint(self.pdf, "--max-blank-band", "0.9", density=True)
        self.assertEqual((code, self.bands(report)), (0, []))

    def test_recorded_exception_covers_only_its_raster(self):
        _, report = lint(self.pdf)
        digest = next(f["raster_sha256"] for f in report["findings"] if f["check"] == "page-blank-band")
        exceptions = self.folder / "exceptions.json"
        exceptions.write_text(json.dumps([{"raster_sha256": digest, "reason": "section end before a full-page table"},
                                          {"raster_sha256": "0" * 64, "reason": "a page that no longer exists"}]))
        code, report = lint(self.pdf, "--blank-exceptions", exceptions)
        self.assertEqual((code, self.bands(report)), (0, [(2, "info")]))
        excepted = next(f for f in report["findings"] if f["check"] == "page-blank-band")
        self.assertEqual(excepted["exception"], "section end before a full-page table")
        unmatched = [f["value"] for f in report["findings"] if f["check"] == "blank-exception-unmatched"]
        self.assertEqual(unmatched, ["0" * 64])
        exceptions.write_text(json.dumps([{"raster_sha256": digest}]))  # no reason recorded
        code, report = lint(self.pdf, "--blank-exceptions", exceptions)
        self.assertEqual(code, 1)
        self.assertEqual(sorted(checks(report, "fail")), ["blank-exceptions-invalid", "page-blank-band"])

    def test_gate_binds_the_exceptions_and_blocks_without_them(self):
        session = self.folder / "session"
        session.mkdir(exist_ok=True)
        _, report = lint(self.pdf)
        digest = next(f["raster_sha256"] for f in report["findings"] if f["check"] == "page-blank-band")
        exceptions = self.folder / "gate-exceptions.json"
        exceptions.write_text(json.dumps([{"raster_sha256": digest, "reason": "recorded in STATE.md"}]))
        for name, extra, blocked in (("plain", [], True), ("excepted", ["--blank-exceptions", exceptions], False)):
            out = self.folder / f"gate-{name}"
            with contextlib.redirect_stdout(io.StringIO()):
                gate.main(["gate", "--session", str(session), "--pdf", str(self.pdf), "--dpi", "40",
                           "--out", str(out), *map(str, extra)])
            record = json.loads((out / "gate.json").read_text())
            self.assertEqual(record["blocked"], blocked, name)
        self.assertEqual(record["inputs"]["blank_exceptions"]["sha256"], gate.sha256_file(exceptions))

@needs("mutool", "pdflatex", "pdffonts", "pdftoppm")
class GateTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)
        self.session = self.folder / "session"
        self.session.mkdir()

    def run_gate(self, pdf, out, *extra):
        with contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["gate", "--session", str(self.session), "--pdf", str(pdf), "--dpi", "40",
                              "--out", str(out), "--approver", "Reviewer", *map(str, extra)])
        return code, json.loads((out / "gate.json").read_text())

    def test_clean_gate_binds_inputs_and_lists_every_page(self):
        pdf, log = latex(self.folder, "Clean text.\\newpage Second page.")
        # A one-line first page is a blank band; this test is about binding, not whitespace.
        code, record = self.run_gate(pdf, self.folder / "gate1", "--log", log, "--max-blank-band", "1")
        self.assertEqual((code, record["blocked"], record["blocking"]), (0, False, []))
        self.assertEqual(record["inputs"]["pdf"]["sha256"], gate.sha256_file(pdf))
        self.assertEqual(record["inputs"]["log"]["sha256"], gate.sha256_file(log))
        for name in ("lint", "packet"):
            output = Path(record["outputs"][name]["path"])
            self.assertEqual(gate.sha256_file(output), record["outputs"][name]["sha256"])
        self.assertEqual(record["review_pages"], [1, 2])
        self.assertEqual(record["contact_sheets"], ["contact-01.png"])
        self.assertFalse(record["ready_for_review"])
        self.assertEqual(record["coverage"]["checks"]["numbers"]["status"], "not_assessed")
        with self.assertRaises(SystemExit):
            self.run_gate(pdf, self.folder / "gate1")

    def test_waivers_bind_one_finding_and_need_a_state_record(self):
        # Review input: a 4 pt footnote and an unrelated 3 pt heading on one page.
        pdf, _ = latex(self.folder, "{\\fontsize{3}{4}\\selectfont\\bfseries Tiny heading}\\par\\bigskip "
                       "{\\fontsize{4}{5}\\selectfont Four point footnote.}")
        code, record = self.run_gate(pdf, self.folder / "blocked")
        self.assertEqual((code, record["blocked"]), (1, True))
        footnote = next(f for f in record["blocking"] if "footnote" in f["message"])
        waiver = {"id": "W1", "check": "font-below-floor", "fingerprint": footnote["fingerprint"],
                  "pdf_sha256": gate.sha256_file(pdf), "reason": "legal footnote size", "approved_by": "Reviewer"}
        others = [{**waiver, "id": "W2", "fingerprint": "0" * 16},          # no such finding
                  {**waiver, "id": "W3", "pdf_sha256": "f" * 64},           # another PDF version
                  {"id": "W4", "check": "font-below-floor", "reason": "x", "approved_by": "y"}]  # malformed
        (self.session / "waivers.json").write_text(json.dumps([waiver, *others]))
        code, record = self.run_gate(pdf, self.folder / "unapproved")  # no STATE.md approval line yet
        self.assertEqual((code, len(record["waivers"]["unapproved"]), record["waivers"]["applied"]), (1, 3, []))
        (self.session / "STATE.md").write_text(
            "# State\n\n- waiver W1: legal footnote size (approved by Reviewer, 2026-10-05)\n"
            "- waiver W2: legal footnote size (approved by Reviewer, 2026-10-05)\n"
            "- waiver W3: legal footnote size (approved by Reviewer, 2026-10-05)\n")
        code, record = self.run_gate(pdf, self.folder / "approved")
        self.assertEqual(code, 1)  # the 3 pt heading still blocks: the waiver names one finding
        self.assertEqual([w["finding"]["fingerprint"] for w in record["waivers"]["applied"]], [footnote["fingerprint"]])
        self.assertEqual(sorted(w["waiver"]["id"] for w in record["waivers"]["unmatched"]), ["W2", "W3"])
        self.assertEqual(len(record["waivers"]["invalid"]), 1)
        self.assertEqual([("Tiny" in f["message"]) for f in record["blocking"]], [True])
        self.assertEqual(record["inputs"]["state"]["sha256"], gate.sha256_file(self.session / "STATE.md"))
        self.assertEqual(record["approver"], "Reviewer")
        # The same waiver is stale once the PDF changes.
        changed, _ = latex(self.folder, "{\\fontsize{4}{5}\\selectfont Four point footnote.} Edited.")
        _, record = self.run_gate(changed, self.folder / "stale")
        self.assertEqual(record["waivers"]["applied"], [])

    def test_malformed_waivers_cannot_remove_a_blocking_finding(self):
        pdf, _ = latex(self.folder, "{\\fontsize{4}{5}\\selectfont Four point footnote.}")
        for index, text in enumerate(("null", "{}", "{broken", "[null]")):
            (self.session / "waivers.json").write_text(text)
            code, record = self.run_gate(pdf, self.folder / f"invalid-waiver-{index}")
            self.assertEqual((code, record["blocked"], record["waivers"]["applied"]), (1, True, []))
            self.assertTrue(record["waivers"]["invalid"])

    def test_only_selected_identity_and_state_line_approve_a_waiver(self):
        pdf, _ = latex(self.folder, "{\\fontsize{4}{5}\\selectfont Four point footnote.}")
        _, record = self.run_gate(pdf, self.folder / "identity-first")
        fail = record["blocking"][0]
        waiver = {"id": "W1", "check": fail["check"], "fingerprint": fail["fingerprint"],
                  "pdf_sha256": gate.sha256_file(pdf), "reason": "accepted footnote", "approved_by": "Reviewer"}
        (self.session / "waivers.json").write_text(json.dumps([waiver]))
        for name, expected in (("Mallory", 1), ("Reviewer", 0)):
            (self.session / "STATE.md").write_text(f"waiver W1: accepted footnote (approved by {name}, 2026-10-05)\n")
            code, record = self.run_gate(pdf, self.folder / name)
            self.assertEqual((code, len(record["waivers"]["applied"]), len(record["waivers"]["unapproved"])),
                              (expected, 1 - expected, expected))
        # Correct state and JSON are insufficient when the CLI selects someone else.
        code, record = self.run_gate(pdf, self.folder / "wrong-cli", "--approver", "Other reviewer")
        self.assertEqual((code, record["waivers"]["applied"]), (1, []))
        self.assertEqual(record["approver"], "Other reviewer")
        waiver["approved_by"] = "Other reviewer"
        (self.session / "waivers.json").write_text(json.dumps([waiver]))
        code, record = self.run_gate(pdf, self.folder / "wrong-json")
        self.assertEqual((code, record["waivers"]["applied"]), (1, []))

    def test_figure_waivers_require_the_figure_hash_and_expire_when_it_changes(self):
        fig = figure(self.folder / "clipped.pdf", lambda f: f.text(.99, .5, "Clipped", fontsize=12))
        pdf, _ = latex(self.folder, r"\includegraphics{clipped.pdf}")
        _, first = self.run_gate(pdf, self.folder / "figure-first")
        self.assertEqual([f["check"] for f in first["blocking"]], ["figure-text-clipped"])
        fail = first["blocking"][0]
        waiver = {"id": "W1", "check": fail["check"], "fingerprint": fail["fingerprint"],
                  "reason": "accepted clipping", "approved_by": "Reviewer"}
        (self.session / "STATE.md").write_text("waiver W1: accepted clipping (approved by Reviewer, 2026-10-05)\n")
        fig_hash, pdf_hash = gate.sha256_file(fig), gate.sha256_file(pdf)
        for selector, digest, code in (("pdf_sha256", pdf_hash, 1), ("figure_sha256", fig_hash, 0)):
            (self.session / "waivers.json").write_text(json.dumps([{**waiver, selector: digest}]))
            actual, record = self.run_gate(pdf, self.folder / selector)
            self.assertEqual((actual, len(record["waivers"]["applied"])), (code, 1 - code))
        # Change PDF metadata only, preserving the clipped geometry/fingerprint and composed PDF.
        script = self.folder / "metadata.js"
        script.write_text('var d = Document.openDocument(scriptArgs[0]); '
                          'd.setMetaData("info:Title", "changed metadata"); d.save(scriptArgs[1]);')
        changed = self.folder / "changed-figure.pdf"
        subprocess.run(["mutool", "run", str(script), str(fig), str(changed)], check=True, capture_output=True)
        shutil.copy(changed, fig)
        self.assertNotEqual(gate.sha256_file(fig), fig_hash)
        self.assertEqual(gate.sha256_file(pdf), pdf_hash)
        for selector, digest in (("pdf_sha256", pdf_hash), ("figure_sha256", fig_hash)):
            (self.session / "waivers.json").write_text(json.dumps([{**waiver, selector: digest}]))
            code, record = self.run_gate(pdf, self.folder / (selector + "-changed"))
            self.assertEqual((code, len(record["waivers"]["applied"]), len(record["waivers"]["unmatched"])),
                             (1, 0, 1))
            self.assertEqual(record["blocking"][0]["fingerprint"], fail["fingerprint"])

    def test_evidence_sources_are_bound_and_rechecked_after_numbers_reads_them(self):
        pdf, _ = latex(self.folder, "Value 7.5.")
        source, values = self.folder / "evidence.json", self.folder / "values.json"
        source.write_text('{"value": 7.5}\n')
        source_hash = gate.sha256_file(source)
        values.write_text(json.dumps({"schema": gate.VALUES_SCHEMA, "schema_version": gate.VALUES_VERSION,
                                     "match_rule": gate.MATCH_RULE,
                                     "sources": {"evidence": {"path": source.name, "sha256": source_hash}},
                                     "values": [{"key": "value", "text": "7.5", "source": "evidence", "page": 1}]}))
        code, record = self.run_gate(pdf, self.folder / "source-control", "--values", values)
        self.assertEqual((code, record["blocked"]), (0, False))
        binding = {"role": "evidence", "path": str(source.resolve()), "sha256": source_hash,
                   "size": source.stat().st_size}
        self.assertEqual(record["inputs"]["sources"], [binding])
        original = gate.page_texts

        def mutate_then_extract(*args, **kwargs):
            source.write_text('{"value": 8.5}\n')
            return original(*args, **kwargs)
        with mock.patch.object(gate, "page_texts", mutate_then_extract):
            code, record = self.run_gate(pdf, self.folder / "source-changed", "--values", values)
        self.assertEqual((code, record["blocked"]), (1, True))
        self.assertEqual(record["inputs"]["sources"], [binding])
        self.assertEqual([(f["check"], f["value"]) for f in record["blocking"]],
                         [("input-changed", str(source.resolve()))])
        numbers = json.loads((self.folder / "source-changed" / "numbers.json").read_text())
        self.assertEqual((numbers["matched_once"], numbers["sources"], numbers["findings"]), (1, [binding], []))

    def test_inputs_changed_during_the_gate_fail(self):
        # Review input: the checked PDF or log is replaced after lint has read it.
        pdf, log = latex(self.folder, "Clean text.")
        swap = self.folder / "swap.pdf"
        shutil.copy(raw_pdf(self.folder / "tiny.pdf", "BT /F1 3 Tf 1 0 0 1 60 110 Tm (tiny) Tj ET"), swap)
        original = gate.build_packet

        def replace_then_render(*args, **kwargs):
            shutil.copy(swap, pdf)
            log.write_text(log.read_text() + "\n! Emergency stop.\n")
            return original(*args, **kwargs)
        with mock.patch.object(gate, "build_packet", replace_then_render):
            code, record = self.run_gate(pdf, self.folder / "toctou", "--log", log)
        self.assertEqual((code, record["blocked"]), (1, True))
        changed = [f["value"] for f in record["blocking"] if f["check"] == "input-changed"]
        self.assertIn(str(pdf.resolve()), changed)
        self.assertIn(str(log.resolve()), changed)
        self.assertIn("packet", changed)  # the packet rendered other bytes than lint checked

    def test_previous_manifest_carries_reviewed_pages_or_blocks_when_refused(self):
        pdf, _ = latex(self.folder, "Page one.\\newpage Page two.")
        self.run_gate(pdf, self.folder / "first", "--max-blank-band", "1")
        manifest = self.folder / "first" / "packet" / "manifest.json"
        reviewed = self.folder / "reviewed.json"
        reviewed.write_text(json.dumps([{"raster_sha256": p["raster_sha256"], "verdict_ref": f"REVIEW p{p['page']}"}
                                        for p in json.loads(manifest.read_text())["pages"]]))
        code, record = self.run_gate(pdf, self.folder / "second", "--previous-manifest", manifest,
                                     "--reviewed", reviewed, "--max-blank-band", "1")
        self.assertEqual((code, record["review_pages"], record["diff"]["carried_pages"]), (0, [], [1, 2]))
        self.assertEqual(record["inputs"]["previous_manifest"]["sha256"], gate.sha256_file(manifest))
        stale = json.loads(manifest.read_text())
        stale["dpi"] = 300
        manifest.write_text(json.dumps(stale))
        code, record = self.run_gate(pdf, self.folder / "third", "--previous-manifest", manifest,
                                     "--reviewed", reviewed, "--max-blank-band", "1")
        self.assertEqual((code, record["blocked"], record["review_pages"]), (1, True, [1, 2]))
        self.assertEqual([f["check"] for f in record["blocking"]], ["diff-refused"])


class WaiverIdentityTest(unittest.TestCase):
    def test_existing_waiver_file_requires_explicit_identity_before_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for data in ("[]", "[{}]", "{broken"):
                (folder / "waivers.json").write_text(data)
                with self.subTest(data=data), mock.patch.object(gate, "lint_report") as lint_mock:
                    with self.assertRaisesRegex(SystemExit, "--approver is required"):
                        gate.main(["gate", "--session", str(folder), "--pdf", str(folder / "absent.pdf"),
                                   "--out", str(folder / "out")])
                    lint_mock.assert_not_called()
                    self.assertFalse((folder / "out").exists())

    def test_identity_must_fit_the_approval_line_format(self):
        with tempfile.TemporaryDirectory() as folder:
            for identity in ("", " ", " Reviewer", "Reviewer\nOther", "Reviewer, Other", "Reviewer (owner)"):
                with self.subTest(identity=identity), self.assertRaisesRegex(SystemExit, "--approver"):
                    gate.main(["gate", "--session", folder, "--pdf", "absent.pdf", "--out", folder + "/out",
                               "--approver", identity])


class OverlapClipTest(unittest.TestCase):
    def glyph(self, line, x0, y0, x1, y1, clip=None):
        return gate.Glyph(line, 10.0, (x0, y1), [(x0, y0), (x1, y0), (x0, y1), (x1, y1)], (1.0, 0.0), "a",
                          run=line, clip=clip)

    def test_overlap_only_in_clipped_ink_is_counted_not_reported(self):
        note = self.glyph(1, 10, 101, 16, 109)  # caption line under a figure box ending at y=100
        unclipped = self.glyph(0, 10, 95, 16, 105)
        self.assertEqual(len(gate.check_overlap(1, [unclipped, note])[0]), 1)
        cut = self.glyph(0, 10, 95, 16, 105, clip=(0, 0, 200, 100))
        self.assertEqual(gate.check_overlap(1, [cut, note]), ([], 1))
        # The caption's own clip does not hide the figure glyph's visible ink.
        other = self.glyph(1, 10, 96, 16, 104, clip=(0, 0, 200, 300))
        findings, hidden = gate.check_overlap(1, [cut, other])
        self.assertEqual((len(findings), hidden, findings[0]["clipped"]), (1, 0, True))


class LogParsingTest(unittest.TestCase):
    def test_log_and_blg_rules(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "doc.log"
            log.write_text("\n".join([
                "Overfull \\hbox (0.5pt too wide) in paragraph at lines 3--4",
                "Overfull \\vbox (12.0pt too high) has occurred while \\output is active",
                "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.",
                "Package: rerunfilecheck 2025-06-21 v1.11 Rerun checks for auxiliary files (HO)",
                "LaTeX Warning: Citation `key' on page 2 undefined on input line 7.",
                "LaTeX Warning: File `fig.pdf' not found on input line 9.",
                "No file doc.toc.",
                "./doc.tex:1: Undefined control sequence.",
                "File: graphicx.sty 2021/09/16 v1.2d Enhanced LaTeX Graphics (DPC,SPQR)",
            ]) + "\n")
            blg = Path(folder) / "doc.blg"
            blg.write_text("[12] Biber.pm:131> WARN - Duplicate entry key 'a'\n"
                           "[13] Utils.pm:410> ERROR - Cannot find 'doc.bcf'!\n")
            results = gate.check_log(log)
            self.assertEqual(results[1]["source"], f"{log}:2")
            found = [(f["check"], f["severity"]) for f in results]
            self.assertEqual(found, [
                ("log-overfull", "flag"), ("log-overfull", "fail"), ("log-rerun", "fail"),
                ("log-undefined-citation", "fail"), ("log-missing-file", "fail"), ("log-missing-file", "flag"),
                ("log-error", "fail")])
            self.assertEqual([(f["check"], f["severity"]) for f in gate.check_blg(blg)],
                             [("blg-warn", "flag"), ("blg-error", "fail")])

    def test_wrapped_include_records(self):
        with tempfile.TemporaryDirectory() as folder:
            name = "figures/" + "x" * 80 + ".pdf"
            record = f"<{name}, id=8, 10pt x 10pt>"
            log = Path(folder) / "doc.log"
            log.write_text(record[:79] + "\n" + record[79:] + "\n")
            self.assertEqual(gate.log_figures(log), [(Path(folder) / name).resolve()])

    def test_include_records_beside_an_aux_dir(self):
        # latexmk aux_dir: the log is in build/, TeX resolved names from the source directory.
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "report"
            (source / "build").mkdir(parents=True)
            figure_path = Path(folder) / "other" / "fig.pdf"
            figure_path.parent.mkdir()
            figure_path.write_bytes(b"%PDF-1.4\n")
            log = source / "build" / "doc.log"
            log.write_text("<../other/fig.pdf, id=8, 10pt x 10pt>\n")
            self.assertEqual(gate.log_figures(log, [log.parent, source]), [figure_path.resolve()])
            self.assertEqual(gate.log_figures(log), [(log.parent / "../other/fig.pdf").resolve()])


@needs("pdftoppm", "matplotlib")
class PacketTest(unittest.TestCase):
    def test_manifest_and_raster_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            pdf = folder / "book.pdf"
            with matplotlib.rc_context(matplotlib.rcParamsDefault), PdfPages(pdf) as pages:
                for number in range(5):
                    fig = plt.figure(figsize=(2, 3))
                    fig.text(0.2, 0.5, f"Page {number + 1}")
                    pages.savefig(fig)
                    plt.close(fig)
            out = folder / "packet"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["packet", str(pdf), "--out", str(out), "--dpi", "50", "--sheet", "2x2"]), 0)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual((manifest["page_count"], manifest["dpi"], manifest["size"]), (5, 50, pdf.stat().st_size))
            self.assertEqual(manifest["sha256"], gate.sha256_file(pdf))
            self.assertEqual(set(manifest["tools"]), {"pdftoppm", "PIL"})
            self.assertEqual([p["png"] for p in manifest["pages"]], [f"page-{n:03d}.png" for n in range(1, 6)])
            self.assertEqual([s["pages"] for s in manifest["contact_sheets"]], [[1, 2, 3, 4], [5]])
            with Image.open(out / "contact-02.png") as sheet:  # PIL-built 2x2 grid of labelled tiles
                self.assertEqual(sheet.size, (2 * (gate.TILE + 2 * gate.GAP), 2 * (gate.TILE + gate.LABEL + 2 * gate.GAP)))
                self.assertLess(sheet.convert("L").getextrema()[0], 50)  # label text and page ink
            for page in manifest["pages"]:
                self.assertEqual(gate.sha256_file(out / page["png"]), page["png_sha256"])
            first = manifest["pages"][0]
            self.assertNotEqual(first["raster_sha256"], manifest["pages"][1]["raster_sha256"])
            # Same pixels, different PNG metadata and compression: same raster hash.
            resaved = folder / "resaved.png"
            from PIL import PngImagePlugin
            info = PngImagePlugin.PngInfo()
            info.add_text("Comment", "different metadata")
            with Image.open(out / first["png"]) as image:
                image.save(resaved, pnginfo=info, compress_level=1)
            self.assertNotEqual(gate.sha256_file(resaved), first["png_sha256"])
            self.assertEqual(gate.raster_sha256(resaved), first["raster_sha256"])
            with self.assertRaises(SystemExit):
                gate.main(["packet", str(pdf), "--out", str(out)])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["packet", str(pdf), "--out", str(out), "--dpi", "50", "--force"]), 0)
            again = json.loads((out / "manifest.json").read_text())
            self.assertEqual([p["raster_sha256"] for p in again["pages"]],
                             [p["raster_sha256"] for p in manifest["pages"]])


@unittest.skipIf(Image is None, "missing PIL")
class DiffTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)

    def manifest(self, name, shades, dpi=72, mark=None):
        """Write a packet of solid grey pages; `mark` = (page, box) paints a black rectangle."""
        out = self.folder / name
        out.mkdir()
        pages = []
        for number, shade in enumerate(shades, 1):
            image = Image.new("RGB", (40, 60), (shade,) * 3)
            if mark and mark[0] == number:
                image.paste((0, 0, 0), mark[1])
            path = out / f"page-{number:03d}.png"
            image.save(path)
            pages.append({"page": number, "png": path.name, "png_sha256": gate.sha256_file(path),
                          "raster_sha256": gate.raster_sha256(path)})
        manifest = {"pdf": name, "sha256": name, "dpi": dpi, "page_count": len(pages), "pages": pages}
        (out / "manifest.json").write_text(json.dumps(manifest))
        return out / "manifest.json", manifest

    def run_diff(self, old, new, reviewed):
        path = self.folder / "reviewed.json"
        path.write_text(json.dumps(reviewed))
        out = self.folder / "diff.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["diff", str(old), str(new), "--reviewed", str(path), "--json", str(out)])
        return code, json.loads(out.read_text()) if code == 0 else None

    def reviewed(self, manifest):
        return [{"raster_sha256": p["raster_sha256"], "verdict_ref": f"REVIEW.md p{p['page']}"}
                for p in manifest["pages"]]

    def decisions(self, report):
        return [p["decision"] for p in report["pages"]]

    def test_identical_reviewed_pages_carry(self):
        old, before = self.manifest("old", [10, 20, 30])
        new, _ = self.manifest("new", [10, 20, 30])
        code, report = self.run_diff(old, new, self.reviewed(before))
        self.assertEqual(code, 0)
        self.assertEqual(self.decisions(report), ["carry"] * 3)
        self.assertEqual(report["pages"][1]["verdict_ref"], "REVIEW.md p2")
        self.assertIn("sequence", report["note"])

    def test_changed_page_and_neighbours(self):
        old, before = self.manifest("old", [10, 20, 30, 40, 50])
        new, _ = self.manifest("new", [10, 20, 30, 40, 50], mark=(3, (5, 7, 15, 20)))
        _, report = self.run_diff(old, new, self.reviewed(before))
        self.assertEqual(self.decisions(report), ["carry", "neighbour", "changed", "neighbour", "carry"])
        self.assertEqual(report["pages"][2]["changed_bbox_px"], [5, 7, 15, 20])
        self.assertEqual(report["review_pages"], [2, 3, 4])
        self.assertIn("verdict_ref", report["pages"][1])  # preserve prior evidence for continuity recheck

    def test_page_count_change_preserves_unchanged_evidence(self):
        old, before = self.manifest("old", [10, 20, 30])
        new, _ = self.manifest("new", [10, 20, 30, 40])
        _, report = self.run_diff(old, new, self.reviewed(before))
        self.assertEqual(self.decisions(report), ["carry", "carry", "neighbour", "changed"])
        self.assertEqual(report["carried_pages"], [1, 2])

    def test_inserted_pages_in_large_book_do_not_reopen_all_pages(self):
        old, before = self.manifest("old", list(range(240)))
        new, _ = self.manifest("new", list(range(5)) + [250, 251] + list(range(5, 240)))
        _, report = self.run_diff(old, new, self.reviewed(before))
        self.assertEqual(report["review_pages"], [5, 6, 7, 8])
        self.assertEqual(len(report["carried_pages"]), 238)
        self.assertEqual(report["pages"][9]["old_page"], 8)
        self.assertNotIn("changed_bbox_px", report["pages"][5])

    def test_reordering_requires_navigation_but_retains_appearance(self):
        old, before = self.manifest("old", [10, 20, 30])
        new, _ = self.manifest("new", [30, 10, 20])
        _, report = self.run_diff(old, new, self.reviewed(before))
        self.assertEqual(report["review_pages"], [])
        self.assertEqual([p["old_page"] for p in report["pages"]], [3, 1, 2])

    def test_unreviewed_identical_page_does_not_carry(self):
        old, before = self.manifest("old", [10, 20, 30, 40, 50])
        new, _ = self.manifest("new", [10, 20, 30, 40, 50])
        reviewed = [r for r in self.reviewed(before) if r["verdict_ref"] != "REVIEW.md p5"]
        _, report = self.run_diff(old, new, reviewed)
        self.assertEqual(self.decisions(report), ["carry", "carry", "carry", "carry", "unreviewed"])
        self.assertIn("no recorded review", report["pages"][4]["reason"])
        self.assertEqual(report["review_pages"], [5])

    def test_stale_png_or_incomplete_manifest_is_refused(self):
        old, before = self.manifest("old", [255, 255])
        new, after = self.manifest("new", [255, 255])
        Image.new("RGB", (40, 60), (0, 0, 0)).save(new.parent / "page-001.png")  # review input
        with contextlib.redirect_stderr(io.StringIO()) as error:
            code, _ = self.run_diff(old, new, self.reviewed(before))
        self.assertEqual(code, 2)
        self.assertIn("raster hash does not match", error.getvalue())
        for broken in ({**after, "pages": []}, {**after, "pages": after["pages"][::-1]}):
            new.write_text(json.dumps(broken))
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.run_diff(old, new, self.reviewed(before))[0], 2)

    def test_dpi_mismatch_is_refused(self):
        old, before = self.manifest("old", [10], dpi=72)
        new, _ = self.manifest("new", [10], dpi=120)
        with contextlib.redirect_stderr(io.StringIO()) as error:
            code, _ = self.run_diff(old, new, self.reviewed(before))
        self.assertEqual(code, 2)
        self.assertIn("different DPI", error.getvalue())



@unittest.skipIf(Image is None, "missing Pillow")
class ReviewPreflightTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)
        self.packet, _ = DiffTest.manifest(self, "packet", list(range(20)))
        self.pdf = self.folder / "artifact.pdf"
        self.pdf.write_bytes(b"immutable test artifact")
        manifest = json.loads(self.packet.read_text())
        manifest["sha256"] = gate.sha256_file(self.pdf)
        self.packet.write_text(json.dumps(manifest))
        self.inputs = {k: None for k in ("log", "blg", "values", "pagemap", "plan", "previous_manifest")}
        self.inputs["pdf"] = gate.file_record(self.pdf)
        self.record = {"blocked": False, "coverage": {"complete": True}, "inputs": self.inputs,
                       "outputs": {"packet": gate.file_record(self.packet)}, "review_pages": list(range(1, 21))}
        self.gate_path = self.folder / "gate.json"
        self.request_path = self.folder / "request.json"
        self.request = {"model": "economy-vision", "effort": "default", "cost_tier": "economy",
                        "route_reason": "Appearance only; verified image access", "pages": [1, 20],
                        "reading_tasks": "Trace legends and read longest labels",
                        "stop_condition": "Return findings for two representatives; do not expand autonomously",
                        "families": [{"pages": list(range(1, 21)), "samples": [1, 20],
                                      "reason": "One accepted layout; longest labels and signed-tail extrema"}]}

    def run_preflight(self):
        self.gate_path.write_text(json.dumps(self.record))
        self.request["gate_sha256"] = gate.sha256_file(self.gate_path)
        self.request_path.write_text(json.dumps(self.request))
        out = self.folder / "result.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["review-preflight", "--gate", str(self.gate_path),
                              "--request", str(self.request_path), "--json", str(out)])
        return code, json.loads(out.read_text())

    def test_bounded_family_request_passes_without_claiming_all_page_review(self):
        code, result = self.run_preflight()
        self.assertEqual(code, 0)
        self.assertEqual(result["pages"], [1, 20])

    def test_incomplete_checks_block_even_when_lint_unblocked(self):
        self.record["coverage"]["complete"] = False
        self.assertEqual(self.run_preflight()[0], 1)

    def test_omitted_checks_are_not_assessed_and_external_checks_are_bound(self):
        coverage, _ = gate.coverage_report(None, self.inputs)
        self.assertFalse(coverage["complete"])
        declarations = {k: {"status": "not_applicable", "reason": "Synthetic fixture"}
                        for k in coverage["checks"]}
        evidence = self.folder / "checked.json"
        evidence.write_text('{"verdict":"GO"}')
        declarations["numbers"] = {"status": "external", "reason": "Independent printed-value check",
                                   "path": str(evidence), "sha256": gate.sha256_file(evidence),
                                   "pdf_sha256": gate.sha256_file(self.pdf)}
        coverage, bound = gate.coverage_report({"checks": declarations}, self.inputs)
        self.assertTrue(coverage["complete"])
        self.assertEqual(bound, [gate.file_record(evidence)])
        evidence.write_text("changed")
        self.assertFalse(gate.coverage_report({"checks": declarations}, self.inputs)[0]["complete"])

    def test_expensive_inherited_route_and_exhaustive_scope_need_reasons(self):
        self.request["model"] = "claude-opus-5-5"
        self.assertEqual(self.run_preflight()[0], 1)
        self.request["cost_tier"] = "escalated"
        self.assertEqual(self.run_preflight()[0], 1)
        self.request["escalation_reason"] = "Economy review could not resolve overlapping legend glyphs"
        self.assertEqual(self.run_preflight()[0], 0)
        self.request["pages"] = list(range(1, 21))
        self.assertEqual(self.run_preflight()[0], 1)

    def test_unaccounted_candidates_and_unselected_samples_are_rejected(self):
        self.request["families"][0]["pages"] = list(range(1, 20))
        self.request["families"][0]["samples"] = [1]
        self.request["pages"] = [1]
        self.assertEqual(self.run_preflight()[0], 1)
        self.request["families"][0]["pages"] = list(range(1, 21))
        self.request["families"][0]["samples"] = [1, 20]
        self.assertEqual(self.run_preflight()[0], 1)

    def test_stale_artifact_or_pixel_packet_blocks(self):
        self.pdf.write_bytes(b"changed after gate")
        self.assertEqual(self.run_preflight()[0], 1)
        self.pdf.write_bytes(b"immutable test artifact")
        image = self.packet.parent / "page-001.png"
        Image.new("RGB", (40, 60), "red").save(image)
        self.assertEqual(self.run_preflight()[0], 1)

    def test_applied_waiver_state_and_waiver_file_remain_hash_bound(self):
        state = self.folder / "STATE.md"
        waivers = self.folder / "waivers.json"
        state.write_text("waiver W1: accepted layout (approved by Reviewer, 2026-10-05)\n")
        waivers.write_text("[]")
        self.inputs["state"] = gate.file_record(state)
        self.inputs["waivers"] = gate.file_record(waivers)
        self.record["approver"] = "Reviewer"
        self.record["waivers"] = {"applied": [{"waiver": {"id": "W1"}}]}
        self.assertEqual(self.run_preflight()[0], 0)
        original = state.read_text()
        state.write_text("Approval withdrawn.\n")
        code, result = self.run_preflight()
        self.assertEqual(code, 1)
        self.assertTrue(any("stale binding" in error for error in result["errors"]))
        state.write_text(original)
        waivers.write_text("changed")
        self.assertEqual(self.run_preflight()[0], 1)

    def test_coordination_state_can_change_without_applied_waivers(self):
        state = self.folder / "STATE.md"
        state.write_text("Initial coordination.\n")
        self.inputs["state"] = gate.file_record(state)
        state.write_text("Updated coordination.\n")
        self.assertEqual(self.run_preflight()[0], 0)

    def test_malformed_request_fields_fail_with_structured_errors(self):
        cases = [{"families": None}, {"families": [None]},
                 {"families": [{"pages": 1, "samples": [1], "reason": "x"}]},
                 {"families": [{"pages": [1], "samples": [1], "reason": None}]},
                 {"cost_tier": "escalated", "escalation_reason": None},
                 {"pages": list(range(1, 21)), "scope_reason": None}]
        original = dict(self.request)
        for change in cases:
            with self.subTest(change=change):
                self.request = {**original, **change}
                code, result = self.run_preflight()
                self.assertEqual(code, 1)
                self.assertTrue(result["errors"])

    def test_changed_family_cannot_sample_only_carried_pages(self):
        self.record["review_pages"] = [10]
        self.assertEqual(self.run_preflight()[0], 1)
        self.request["pages"] = [10]
        self.request["families"][0]["samples"] = [10]
        self.assertEqual(self.run_preflight()[0], 0)

    def test_near_exhaustive_review_also_needs_scope_reason(self):
        self.request["pages"] = list(range(1, 20))
        self.request["families"][0]["samples"] = [1]
        self.assertEqual(self.run_preflight()[0], 1)
        self.request["scope_reason"] = "Nineteen distinct new layouts with unresolved decoding tasks"
        self.assertEqual(self.run_preflight()[0], 0)


class MatchRuleTest(unittest.TestCase):
    """Pins the copied rule against analyb.printed's documented examples."""

    def test_text_examples(self):
        for line, text, found in [
            ("ptl1  1.001234  0.98", "1.001234", True),
            ("ptl1  11.001234", "1.001234", False),
            ("ptl1  1.0012344", "1.001234", False),
            ("value 1.25. Next", "1.25", True),
            ("value 1.25.5", "1.25", False),
            ("yield \u22123.2", "-3.2", True),
            ("yield 1.23e + 04", "1.23e+04", True),
            ("range 0\u20135", "0-5", True),
            ("row -3.2", "3.2", False),
            ("row \u22123.2", "3.2", False),
            ("row +3.2", "3.2", False),
            ("row 1.25e+04", "1.25", False),
            ("row 1.23e+04", "04", False),
            ("row 1.23e + 04", "04", False),
            ("row 1.23e + 04", "1.23", False),
            ("row 1.23e\u221204", "1.23e-04", True),
            ("row 1,234.5", "234.5", False),
            ("row 1,234.5", "1,234.5", True),
            ("row b77WP", "77", False),
            ("row 12.5%", "12.5", False),
            ("row 12.5 %", "12.5%", True),
            ("row — 3.2", "3.2", True),
            ("row --- 3.2", "3.2", True),
            ("range 0–5", "-5", False),
            ("row - 3.2", "-3.2", True),
            ("row -  3.2", "3.2", False),
            ("row -  3.2", "-3.2", False),
            ("row 12kg", "12kg", False),
            ("row -.5e+04", ".5", False),
            ("row -.5e+04", "04", False),
            ("row − .5e + 04", "-.5e+04", True),
            ("row −٣.٢", "3.2", False),
            ("row −٣.٢", "-3.2", True),
            ("row 1 , 234.5", "234.5", False),
            ("row 1 , 234.5", "1,234.5", True),
            ("row 1 , 23.4", "23.4", False),
            ("row 1,234.5GeV", "1,234.5 GeV", True),
            ("row 1,,234.5", "234.5", False),
            ("row 1e2e3", "3", False),
            ("row 12.5%kg", "12.5", False),
            ("row 12.5%kg", "12.5%kg", False),
            ("row 12.5%3", "3", False),
            ("row 1.2..3", "1.2", False),
            ("row 1..2", "1", False),
            ("row 12 radial bins", "12", True),
            ("row 12 radial bins", "12 radial bins", True),
            ("row 12\tnsamples", "12", True),
            ("row 12.", "12", True),
        ]:
            with self.subTest(line=line, text=text):
                self.assertIs(bool(gate.find_printed([line], text)), found)

    def test_context_examples(self):
        lines = ["ttbar 12 3", "single top 7 12", "ttbar_extra 5", "single_top 9"]
        self.assertEqual(gate.find_printed(lines, "12", context="ttbar"), [0])
        self.assertEqual(gate.find_printed(lines, "3", context="single_top"), [])
        self.assertEqual(gate.find_printed(lines, "7", context="single_top"), [1])  # '_' extracts as a space
        self.assertEqual(gate.find_printed(lines, "9", context="single top"), [3])
        self.assertEqual(gate.find_printed(lines, "5", context="ttbar"), [])
        self.assertEqual(gate.find_printed(lines, "5", context="ttbar_extra"), [2])
        self.assertEqual(gate.find_printed(lines, "12", context="tt"), [])
        # Documented limit: the cell holding the value is not verified.
        self.assertEqual(gate.find_printed(["ttbar 7 \u00b1 12"], "12", context="ttbar"), [0])
        self.assertEqual(gate.find_printed(["ttbar 7 \u00b1 12"], "7", context="ttbar"), [0])

    def test_rule_string_is_analyb_v4(self):
        self.assertEqual(gate.VALUES_VERSION, 4)
        self.assertTrue(gate.MATCH_RULE.startswith("v4; fold unary minus"))
        self.assertTrue(gate.MATCH_RULE.endswith("only row presence, not cells or arithmetic, is verified"))

    def test_plan_key_tokens(self):
        slot = {"figure": "figs/v3-J1_met_native_absolute_l.pdf"}
        self.assertTrue(gate.plan_matches({"key": "met"}, slot))
        self.assertTrue(gate.plan_matches({"key": "J1_met"}, slot))
        self.assertFalse(gate.plan_matches({"key": "met"}, {"figure": "figs/J1_mtlepmet_native.pdf"}))


TABLE = r"""\begin{tabular}{lrr}
ttbar & $1.23e{+}04$ & $\pm 12$ \\
single\_top & $-3.2$ & $\pm 12$ \\
\end{tabular}
\newpage Second page text 7.5."""


@needs("pdflatex", "pdftotext")
class NumbersTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)
        self.pdf, _ = latex(self.folder, TABLE)
        self.source = self.folder / "evidence.json"
        self.source.write_text('{"ratio": 1}\n')

    def manifest(self, records, **changes):
        record = {"schema": "analyb.printed_values", "schema_version": gate.VALUES_VERSION, "producer": "test",
                  "match_rule": gate.MATCH_RULE,
                  "sources": {"evidence": {"path": "evidence.json", "sha256": gate.sha256_file(self.source)}},
                  "values": [{"key": k, "value": None, "text": t, "source": "evidence", "context": c,
                              "section": None, "page": p} for k, t, c, p in records]}
        record.update(changes)
        path = self.folder / "values.json"
        path.write_text(json.dumps(record))
        return path

    def run_numbers(self, manifest):
        out = self.folder / "numbers.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["numbers", str(self.pdf), str(manifest), "--json", str(out)])
        return code, json.loads(out.read_text())

    def test_values_found_missing_and_ambiguous(self):
        manifest = self.manifest([("tt/value", "1.23e+04", "ttbar", None), ("st/value", "-3.2", "single_top", None),
                                  ("late", "7.5", None, 2), ("tt/error", "12", "ttbar", None),
                                  ("any/error", "12", None, None), ("wrong", "-3.3", "single_top", None),
                                  ("wrong-page", "7.5", None, 1)])
        code, report = self.run_numbers(manifest)
        self.assertEqual(code, 1)
        found = sorted((f["check"], f["key"]) for f in report["findings"])
        self.assertEqual(found, [("value-ambiguous", "any/error"), ("value-missing", "wrong"),
                                 ("value-missing", "wrong-page")])
        self.assertEqual(report["matched_once"], 4)

    def test_stale_source_and_invalid_manifest_fail(self):
        manifest = self.manifest([("tt/value", "1.23e+04", "ttbar", None)])
        self.source.write_text('{"ratio": 2}\n')
        code, report = self.run_numbers(manifest)
        self.assertEqual((code, checks(report)), (1, ["source-stale"]))
        code, report = self.run_numbers(self.manifest([], schema_version=1))
        self.assertEqual((code, checks(report)), (1, ["values-invalid"]))

    def test_invalid_page_and_unregistered_source_records_fail(self):
        for page in (0, -1, True, "2", 1.5, [], {}):
            with self.subTest(page=page):
                code, report = self.run_numbers(self.manifest([("late", "7.5", None, page)]))
                self.assertEqual((code, report["matched_once"], checks(report)), (1, 0, ["values-invalid"]))
        code, report = self.run_numbers(self.manifest([("late", "7.5", None, 2)], sources={}))
        self.assertEqual((code, report["matched_once"], checks(report)), (1, 0, ["values-invalid"]))
        # Registered sources and positive pages, or null pages/sources, are valid.
        self.assertEqual(self.run_numbers(self.manifest([("late", "7.5", None, 2)]))[0], 0)
        path = self.manifest([("late", "7.5", None, None)], sources={})
        data = json.loads(path.read_text())
        data["values"][0]["source"] = None
        path.write_text(json.dumps(data))
        self.assertEqual(self.run_numbers(path)[0], 0)
        self.assertIn("value-missing", checks(self.run_numbers(self.manifest([("late", "7.5", None, 3)]))[1]))

    def test_malformed_manifest_and_record_shapes_fail_without_crashing(self):
        for changes in ({"sources": []}, {"sources": {"evidence": None}}, {"values": [None]},
                        {"values": [{"key": "x", "text": 7.5}]},
                        {"values": [{"key": "x", "text": "7.5", "source": []}]},
                        {"values": [{"key": "x", "text": "7.5", "context": 2}]},
                        {"values": [{"key": "x", "text": "   "}]},
                        {"values": [{"key": "x", "text": "7.5", "context": "---"}]},
                        {"values": [{"key": "x", "text": "7.5", "context": ""}]}):
            with self.subTest(changes=changes):
                code, report = self.run_numbers(self.manifest([], **changes))
                self.assertEqual((code, checks(report)), (1, ["values-invalid"]))
        path = self.manifest([])
        for text in ("[]", "null", "{broken"):
            with self.subTest(text=text):
                path.write_text(text)
                self.assertEqual(self.run_numbers(path)[0], 1)

    @needs("mutool", "pdffonts", "pdftoppm")
    def test_malformed_value_strings_write_blocking_full_gate_reports(self):
        session = self.folder / "session"
        session.mkdir()
        (session / "STATE.md").write_text("No waivers.\n")
        for index, (text, context) in enumerate((("   ", None), ("7.5", "---"))):
            manifest = self.manifest([("malformed", text, context, None)])
            out = self.folder / f"invalid-gate-{index}"
            with contextlib.redirect_stdout(io.StringIO()):
                code = gate.main(["gate", "--session", str(session), "--pdf", str(self.pdf),
                                  "--values", str(manifest), "--dpi", "40", "--out", str(out)])
            report = json.loads((out / "gate.json").read_text())
            numbers = json.loads((out / "numbers.json").read_text())
            self.assertEqual(code, 1)
            self.assertTrue(report["blocked"])
            self.assertEqual(checks(numbers), ["values-invalid"])
            self.assertEqual(numbers["matched_once"], 0)


def compact_book(folder, sections):
    """A compiled two-column book in the layout of analyb's write_compact_plotbook."""
    lines = [r"\documentclass[a4paper,10pt]{article}", r"\usepackage[margin=12mm]{geometry}",
             r"\usepackage{graphicx}", r"\usepackage[T1]{fontenc}", r"\usepackage{lmodern}",
             r"\setlength{\parindent}{0pt}", r"\begin{document}"]
    for number, (heading, entries) in enumerate(sections):
        if number:
            lines.append(r"\clearpage")
        lines.append(r"{\large\bfseries " + heading + r"}\par\medskip")
        for index, (name, caption) in enumerate(entries):
            if name not in [p.name for p in folder.glob("*.pdf")]:
                figure(folder / name, lambda f: f.add_subplot().plot([0, 1]), size=(4.5, 5.4))
            lines += [r"\hfill" if index % 2 else "", r"\begin{minipage}[t]{0.485\textwidth}\centering",
                      r"\includegraphics[width=\linewidth,height=0.27\textheight,keepaspectratio]{" + name + "}",
                      r"\par\smallskip{\small " + caption + r"}", r"\end{minipage}"]
            if index % 2:
                lines.append(r"\par\bigskip")
    lines.append(r"\end{document}")
    (folder / "book.tex").write_text("\n".join(lines) + "\n")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "book.tex"], cwd=folder, capture_output=True)
    return folder / "book.pdf"


def page_map(sections, **changes):
    pages = [{"page": n + 1, "section": heading, "rows": 3,
              "slots": [{"figure": name, "caption": caption, "row": i // 2 + 1, "column": i % 2 + 1}
                        for i, (name, caption) in enumerate(entries)]}
             for n, (heading, entries) in enumerate(sections)]
    record = {"schema": "analyb.plotbook_page_map", "schema_version": 1, "tex": "book.tex", "pdf": "book.pdf",
              "page_count": len(pages), "pages": pages}
    record.update(changes)
    return record


BOOK = [("Particle level", [("ptl1_yield.pdf", "Leading lepton yield"), ("ptl1_shape.pdf", "Leading lepton shape")]),
        ("Native cutflows", [("met_yield.pdf", "Missing energy yield")])]


@needs("mutool", "pdflatex", "pdftotext", "pdffonts", "matplotlib")
class InventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp())
        cls.pdf = compact_book(cls.folder, BOOK)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder)

    def run_inventory(self, record, plan=None):
        path = self.folder / "book.pagemap.json"
        path.write_text(json.dumps(record))
        argv = ["inventory", str(self.pdf), str(path), "--json", str(self.folder / "inventory.json")]
        if plan is not None:
            (self.folder / "plan.json").write_text(json.dumps(plan))
            argv += ["--plan", str(self.folder / "plan.json")]
        with contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(argv)
        return code, json.loads((self.folder / "inventory.json").read_text())

    def test_matching_book_passes(self):
        code, report = self.run_inventory(page_map(BOOK))
        self.assertEqual((code, report["findings"]), (0, []))

    def test_figure_order_membership_and_page_count(self):
        swapped = [(BOOK[0][0], BOOK[0][1][::-1]), BOOK[1]]
        _, report = self.run_inventory(page_map(swapped))
        self.assertEqual([(f["check"], f["page"]) for f in report["findings"]], [("figure-misordered", 1), ("figure-misplaced", 1),
                          ("caption-missing", 1), ("caption-missing", 1)])
        moved = [(BOOK[0][0], BOOK[0][1][:1]), (BOOK[1][0], BOOK[0][1][1:] + BOOK[1][1])]
        _, report = self.run_inventory(page_map(moved))
        self.assertEqual(sorted((f["check"], f["page"]) for f in report["findings"]),
                         [("caption-missing", 2), ("caption-missing", 2), ("figure-extra", 1), ("figure-missing", 2)])
        _, report = self.run_inventory(page_map(BOOK, page_count=3))
        self.assertEqual(checks(report), ["pagemap-invalid"])
        _, report = self.run_inventory(page_map(BOOK[:1]))
        self.assertEqual(checks(report), ["page-count"])
        _, report = self.run_inventory(page_map(BOOK, schema_version=7))
        self.assertEqual(checks(report), ["pagemap-invalid"])

    def test_page_identities_must_be_unique_positive_and_ordered(self):
        for identities in ((1, 1), (2, 1), (0, 2), (-1, 2), (1, True), (1, "2")):
            with self.subTest(identities=identities):
                record = page_map(BOOK)
                for entry, identity in zip(record["pages"], identities):
                    entry["page"] = identity
                code, report = self.run_inventory(record)
                self.assertEqual((code, checks(report)), (1, ["pagemap-invalid"]))

    def test_slot_positions_and_malformed_maps_fail_closed(self):
        for field, value in (("row", 0), ("row", 3), ("column", 2), ("column", True), ("figure", [])):
            with self.subTest(field=field, value=value):
                record = page_map(BOOK)
                record["pages"][0]["slots"][0][field] = value
                self.assertEqual(self.run_inventory(record)[0], 1)
        for record in (None, [], {"schema": gate.PAGEMAP_SCHEMA}, page_map(BOOK, page_count=-1)):
            self.assertEqual(self.run_inventory(record)[0], 1)
        for plan in ({}, [None], [{"key": []}], [{"figure": "x", "group": []}], [{"figure": None, "key": "met"}]):
            self.assertIn("plan-invalid", checks(self.run_inventory(page_map(BOOK), plan)[1]))
        self.run_inventory(page_map(BOOK))
        map_path, plan_path = self.folder / "book.pagemap.json", self.folder / "plan.json"
        for text in ("null", "{broken"):
            map_path.write_text(text)
            self.assertEqual(checks(gate.inventory_report(self.pdf, map_path)), ["pagemap-invalid"])
        map_path.write_text(json.dumps(page_map(BOOK)))
        for text in ("null", "{broken"):
            plan_path.write_text(text)
            self.assertEqual(checks(gate.inventory_report(self.pdf, map_path, plan_path)), ["plan-invalid"])

    def test_captions_match_exactly_in_their_own_figure_regions(self):
        swapped = page_map(BOOK)
        captions = [slot["caption"] for slot in swapped["pages"][0]["slots"]]
        for slot, caption in zip(swapped["pages"][0]["slots"], reversed(captions)):
            slot["caption"] = caption
        code, report = self.run_inventory(swapped)
        self.assertEqual((code, checks(report)), (1, ["caption-missing", "caption-missing"]))
        substring = page_map(BOOK)
        substring["pages"][0]["slots"][0]["caption"] = "Leading lepton"
        code, report = self.run_inventory(substring)
        self.assertEqual((code, checks(report)), (1, ["caption-missing"]))

    def test_physical_transforms_and_extra_or_missing_labels_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            entries = [("upper.pdf", "Upper yield"), ("lower.pdf", "Lower shape"),
                       ("third.pdf", "Third yield"), ("fourth.pdf", "Fourth shape")]
            sections = [("Physical placements", entries)]
            # The figure itself contains the expected caption; it cannot supply a missing caption below it.
            figure(folder / "upper.pdf", lambda f: f.text(.2, .5, "Upper yield", fontsize=12))
            pdf = compact_book(folder, sections)
            map_path = folder / "book.pagemap.json"
            map_path.write_text(json.dumps(page_map(sections)))
            self.assertEqual(gate.inventory_report(pdf, map_path)["findings"], [])
            # Preserve the Do/content order while exchanging only the physical CTMs.
            script = folder / "swap.js"
            script.write_text(r'''var d = Document.openDocument(scriptArgs[0]);
var p = d.loadPage(0).getObject(), content = p.get("Contents").readStream().asString();
var commands = content.match(/1 0 0 1 [-.0-9]+ [-.0-9]+ cm\s*q\s*[-.0-9 ]+ cm\s*q\s*[-.0-9 ]+ cm\s*\/Im\d+ Do\s*Q\s*Q\s*1 0 0 1 [-.0-9]+ [-.0-9]+ cm/g);
var a = Number(scriptArgs[2]), b = Number(scriptArgs[3]);
var drawA = commands[a].match(/\/Im\d+ Do/)[0], drawB = commands[b].match(/\/Im\d+ Do/)[0];
content = content.replace(commands[a], "SWAP_A").replace(commands[b], "SWAP_B");
content = content.replace("SWAP_A", commands[b].replace(drawB, drawA)).replace("SWAP_B", commands[a].replace(drawA, drawB));
p.put("Contents", d.addStream(content, {})); d.save(scriptArgs[1]);''')
            for a, b in ((0, 1), (0, 2)):
                target = folder / f"swapped-{a}-{b}.pdf"
                subprocess.run(["mutool", "run", str(script), str(pdf), str(target), str(a), str(b)],
                               check=True, capture_output=True)
                report = gate.inventory_report(target, map_path)
                self.assertIn("figure-misplaced", checks(report, "fail"))
                self.assertNotIn("figure-misordered", checks(report))
            cases = [("Physical placements extra", entries, {"heading-missing"}),
                     ("Physical placements", [("upper.pdf", "Upper yield extra"), *entries[1:]], {"caption-missing"}),
                     ("Physical placements", [("upper.pdf", ""), ("lower.pdf", "Upper yield Lower shape"), *entries[2:]],
                      {"caption-missing"}),
                     ("Physical placements", [("upper.pdf", "Upper yield Upper yield"), *entries[1:]],
                      {"caption-missing"})]
            for heading, actual_entries, expected in cases:
                with self.subTest(heading=heading, captions=actual_entries):
                    candidate = compact_book(folder, [(heading, actual_entries)])
                    self.assertEqual(set(checks(gate.inventory_report(candidate, map_path), "fail")), expected)

    def test_wrapped_labels_and_unequal_figure_heights_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            entries = [("wide.pdf", "A long caption that wraps over several lines and identifies only the wide figure"),
                       ("tall.pdf", "A tall figure caption"), ("wide.pdf", "Another wide figure"),
                       ("tall.pdf", "Another tall figure")]
            figure(folder / "wide.pdf", lambda f: f.text(.2, .5, "wide", fontsize=12), size=(4, 2))
            figure(folder / "tall.pdf", lambda f: f.text(.2, .5, "tall", fontsize=12), size=(2, 4))
            sections = [("A long section heading for geometry checks", entries)]
            pdf = compact_book(folder, sections)
            path = folder / "book.pagemap.json"
            path.write_text(json.dumps(page_map(sections)))
            self.assertEqual(gate.inventory_report(pdf, path)["findings"], [])

    def test_missing_heading_and_caption(self):
        renamed = [("Detector level", [(BOOK[0][1][0][0], "Subleading lepton yield"), BOOK[0][1][1]]), BOOK[1]]
        _, report = self.run_inventory(page_map(renamed))
        self.assertEqual(sorted(checks(report, "fail")), ["caption-missing", "heading-missing"])

    def test_plan_coverage_and_group_split(self):
        plan = [{"key": "ptl1", "group": "lepton"}, {"key": "met", "group": "lepton"},
                {"key": "mtw"}, {"figure": "met_yield.pdf"}]
        code, report = self.run_inventory(page_map(BOOK), plan)
        self.assertEqual(code, 1)
        self.assertEqual(sorted((f["check"], f["severity"], f["value"]) for f in report["findings"]),
                         [("coverage-missing", "fail", "mtw"), ("group-split", "flag", [1, 2])])

    def test_gate_runs_numbers_and_inventory_and_binds_them(self):
        session = self.folder / "session"
        session.mkdir(exist_ok=True)
        (self.folder / "book.pagemap.json").write_text(json.dumps(page_map(BOOK)))
        values = self.folder / "values.json"
        values.write_text(json.dumps({"schema": "analyb.printed_values", "schema_version": gate.VALUES_VERSION, "producer": "t",
                                      "match_rule": gate.MATCH_RULE, "sources": {},
                                      "values": [{"key": "missing", "value": 1.0, "text": "9.87", "source": None,
                                                  "context": None, "section": None, "page": None}]}))
        out = self.folder / "gate"
        with contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["gate", "--session", str(session), "--pdf", str(self.pdf), "--dpi", "30",
                              "--values", str(values), "--pagemap", str(self.folder / "book.pagemap.json"),
                              "--out", str(out)])
        record = json.loads((out / "gate.json").read_text())
        self.assertEqual((code, record["blocked"]), (1, True))
        self.assertEqual({f["check"] for f in record["blocking"]} & {"value-missing", "figure-missing"},
                         {"value-missing"})
        self.assertEqual(record["inputs"]["values"]["sha256"], gate.sha256_file(values))
        self.assertIsNotNone(record["inputs"]["pagemap"])
        self.assertTrue(record["outputs"]["numbers"] and record["outputs"]["inventory"])


if __name__ == "__main__":
    unittest.main()
