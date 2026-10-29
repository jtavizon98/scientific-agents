import importlib.util
import posixpath
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.dom import minidom


SKILL = Path(__file__).parents[1] / "skills" / "presentations"
SPEC = importlib.util.spec_from_file_location("export_pptx", SKILL / "scripts" / "export_pptx.py")
export = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(export)
TOOLS = ("pdflatex", "mutool", "pdfinfo", "pdftotext", "kpsewhich")


def pdflatex(folder, *argv):
    subprocess.run(["pdflatex", "-interaction=nonstopmode", *argv], cwd=folder, capture_output=True, text=True)


@unittest.skipIf([t for t in TOOLS if shutil.which(t) is None]
                 or subprocess.run(["kpsewhich", "beamerthememetropolis.sty"], capture_output=True).returncode,
                 "needs pdflatex, the metropolis theme, MuPDF and poppler")
class ExportPptxTest(unittest.TestCase):
    """Build the template deck with and without notes, export it and check the package."""

    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp())
        deck = cls.folder / "deck"
        shutil.copytree(SKILL / "references" / "template", deck)
        pdflatex(deck, "deck.tex")
        pdflatex(deck, "-jobname=deck-notes", r"\def\withnotes{}\input{deck}")
        cls.pdf, cls.notes = deck / "deck.pdf", deck / "deck-notes.pdf"
        cls.pptx = cls.folder / "deck.pptx"
        export.main([str(cls.pdf), "--notes", str(cls.notes), "--out", str(cls.pptx), "--dpi", "60"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder)

    def test_package_is_complete(self):
        pages = len(export.page_sizes(self.pdf))
        with zipfile.ZipFile(self.pptx) as archive:
            names = set(archive.namelist())
            types = archive.read("[Content_Types].xml").decode()
            for name in names:
                if name.endswith((".xml", ".rels")):
                    minidom.parseString(archive.read(name))
                if name.endswith(".xml") and name != "[Content_Types].xml":
                    self.assertIn(f'PartName="/{name}"', types)
                if name.endswith(".rels"):
                    base = posixpath.dirname(posixpath.dirname(name))
                    for target in re.findall(r'Target="([^"]+)"', archive.read(name).decode()):
                        self.assertIn(posixpath.normpath(posixpath.join(base, target)), names, name)
            slides = [n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
            self.assertEqual(len(slides), pages)
            notes = archive.read("ppt/notesSlides/notesSlide2.xml").decode()
        self.assertIn("Say why the audience should care in two sentences.", notes)

    def test_notes_must_match_the_deck(self):
        with self.assertRaises(SystemExit):
            export.read_notes(self.notes, export.page_sizes(self.notes))  # notes pages are not twice themselves
        with self.assertRaises(SystemExit):
            export.read_notes(self.notes, export.page_sizes(self.pdf)[:-1])

    def test_paragraphs_join_wrapped_lines(self):
        xml = export.paragraphs("First line\nwraps here.\n\nSecond & last.\n")
        self.assertEqual(re.findall(r"<a:t>([^<]*)</a:t>", xml), ["First line wraps here.", "Second &amp; last."])

    @unittest.skipIf(shutil.which("soffice") is None, "needs LibreOffice")
    def test_libreoffice_opens_it(self):
        out = self.folder / "lo"
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out), str(self.pptx)],
                       capture_output=True, timeout=180)
        self.assertEqual(len(export.page_sizes(out / "deck.pdf")), len(export.page_sizes(self.pdf)))


if __name__ == "__main__":
    unittest.main()
