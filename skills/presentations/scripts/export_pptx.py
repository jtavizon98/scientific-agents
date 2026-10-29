#!/usr/bin/env python3
"""Export a slide PDF to a PowerPoint file with one picture per page.

  export_pptx.py DECK.pdf --out DECK.pptx [--notes DECK-notes.pdf] [--dpi 200]

Each PDF page becomes one slide holding a PNG of that page, so overlays stay
separate slides and a click advances them as in a PDF viewer. The slide size
is 13.333 in wide with the PDF's aspect ratio. The Beamer source stays the
only source; the .pptx is for rooms that need PowerPoint, not for editing.

`--notes` takes the same deck built with `show notes on second screen=right`
(see the presentations template). It must have the same page count, each page
twice as wide as the slide; the text of each page's right half becomes that
slide's speaker notes, one paragraph per text block.

Needs `mutool` (MuPDF) to render pages and `pdftotext` (poppler) to read
notes. Uses only the Python standard library.
"""
import argparse
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

SLIDE_WIDTH_EMU = 12192000  # 13.333 in, PowerPoint's 16:9 width
NOTES_SIZE = (6858000, 9144000)
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
CT = "application/vnd.openxmlformats-officedocument."
HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
GROUP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
         '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
         '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')
CLRMAP = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
          'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" '
          'folHlink="folHlink"/>')
SOLID = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
THEME = (HEAD + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Plain">'
         '<a:themeElements><a:clrScheme name="Plain">'
         '<a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
         '<a:dk2><a:srgbClr val="4C4F69"/></a:dk2><a:lt2><a:srgbClr val="EFF1F5"/></a:lt2>'
         + "".join(f'<a:accent{i}><a:srgbClr val="{c}"/></a:accent{i}>' for i, c in
                   enumerate(("1E66F5", "8839EF", "40A02B", "FE640B", "179299", "D20F39"), 1))
         + '<a:hlink><a:srgbClr val="04A5E5"/></a:hlink><a:folHlink><a:srgbClr val="8839EF"/></a:folHlink>'
         '</a:clrScheme><a:fontScheme name="Plain">'
         '<a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
         '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
         '</a:fontScheme><a:fmtScheme name="Plain">'
         '<a:fillStyleLst>' + SOLID * 3 + '</a:fillStyleLst>'
         '<a:lnStyleLst>' + f'<a:ln w="6350">{SOLID}</a:ln>' * 3 + '</a:lnStyleLst>'
         '<a:effectStyleLst>' + '<a:effectStyle><a:effectLst/></a:effectStyle>' * 3 + '</a:effectStyleLst>'
         '<a:bgFillStyleLst>' + SOLID * 3 + '</a:bgFillStyleLst>'
         '</a:fmtScheme></a:themeElements></a:theme>')


def rels(*items):
    """Relationships part from (id, type, target) triples."""
    body = "".join(f'<Relationship Id="{i}" Type="{REL}{t}" Target="{target}"/>' for i, t, target in items)
    return HEAD + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{body}</Relationships>'


def placeholder(shape_id, name, kind, box, body=""):
    x, y, cx, cy = box
    index = ' idx="1"' if kind == "body" else ""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="{kind}"{index}/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            + (f'<p:txBody><a:bodyPr/><a:lstStyle/>{body}</p:txBody>' if kind == "body" else "") + '</p:sp>')


IMAGE_BOX = (381000, 685800, 6096000, 3429000)
NOTES_BOX = (685800, 4343400, 5486400, 4114800)


def paragraphs(text):
    """One paragraph per blank-line-separated block, its wrapped lines joined for PowerPoint to rewrap."""
    blocks = [" ".join(line.strip() for line in block.splitlines() if line.strip())
              for block in re.split(r"\n\s*\n", text)]
    return "".join(f'<a:p><a:r><a:rPr lang="en-US"/><a:t>{escape(b)}</a:t></a:r></a:p>' for b in blocks if b) \
        or '<a:p><a:endParaRPr lang="en-US"/></a:p>'


def page_sizes(pdf: Path):
    """(width, height) in points for every page, from pdfinfo."""
    out = subprocess.run(["pdfinfo", "-f", "1", "-l", "100000", str(pdf)], capture_output=True, text=True,
                         check=True).stdout
    return [tuple(float(v) for v in line.split(":", 1)[1].split()[0:3:2])
            for line in out.splitlines() if line.startswith("Page") and "size:" in line]


def render(pdf: Path, folder: Path, dpi: int):
    subprocess.run(["mutool", "draw", "-q", "-r", str(dpi), "-o", str(folder / "page-%d.png"), str(pdf)],
                   check=True, capture_output=True)
    return sorted(folder.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1]))


def read_notes(notes: Path, sizes):
    """Text of the right half of every page of the notes build."""
    noted = page_sizes(notes)
    if len(noted) != len(sizes):
        raise SystemExit(f"{notes} has {len(noted)} pages, the deck {len(sizes)}: build both from one source")
    texts = []
    for number, ((width, height), (slide_width, _)) in enumerate(zip(noted, sizes), 1):
        if abs(width - 2 * slide_width) > 1:
            raise SystemExit(f"{notes} page {number} is {width:.0f} pt wide, not twice the slide; "
                             "build it with show notes on second screen=right")
        texts.append(subprocess.run(
            ["pdftotext", "-f", str(number), "-l", str(number), "-x", str(int(slide_width)), "-y", "0",
             "-W", str(int(width - slide_width) + 1), "-H", str(int(height) + 1), str(notes), "-"],
            capture_output=True, text=True, check=True).stdout.replace("\f", ""))
    return texts


def write_pptx(out: Path, images, size, notes=None):
    cx = SLIDE_WIDTH_EMU
    cy = round(cx * size[1] / size[0])
    count = len(images)
    parts = {}
    types = [("/ppt/presentation.xml", "presentationml.presentation.main+xml"),
             ("/ppt/slideMasters/slideMaster1.xml", "presentationml.slideMaster+xml"),
             ("/ppt/slideLayouts/slideLayout1.xml", "presentationml.slideLayout+xml"),
             ("/ppt/theme/theme1.xml", "theme+xml")]
    present_rels = [("rId1", "slideMaster", "slideMasters/slideMaster1.xml"), ("rId2", "theme", "theme/theme1.xml")]
    notes_master = ""
    if notes is not None:
        types += [("/ppt/notesMasters/notesMaster1.xml", "presentationml.notesMaster+xml"),
                  ("/ppt/theme/theme2.xml", "theme+xml")]
        present_rels.append(("rId3", "notesMaster", "notesMasters/notesMaster1.xml"))
        notes_master = '<p:notesMasterIdLst><p:notesMasterId r:id="rId3"/></p:notesMasterIdLst>'
        parts["ppt/notesMasters/notesMaster1.xml"] = (
            HEAD + f'<p:notesMaster {NS}><p:cSld><p:spTree>{GROUP}'
            + placeholder(2, "Slide Image Placeholder", "sldImg", IMAGE_BOX)
            + placeholder(3, "Notes Placeholder", "body", NOTES_BOX, paragraphs(""))
            + f'</p:spTree></p:cSld>{CLRMAP}</p:notesMaster>')
        parts["ppt/notesMasters/_rels/notesMaster1.xml.rels"] = rels(("rId1", "theme", "../theme/theme2.xml"))
        parts["ppt/theme/theme2.xml"] = THEME
    slide_ids = ""
    for number, image in enumerate(images, 1):
        rid = f"rId{100 + number}"
        present_rels.append((rid, "slide", f"slides/slide{number}.xml"))
        slide_ids += f'<p:sldId id="{255 + number}" r:id="{rid}"/>'
        types.append((f"/ppt/slides/slide{number}.xml", "presentationml.slide+xml"))
        parts[f"ppt/media/page{number}.png"] = image.read_bytes()
        parts[f"ppt/slides/slide{number}.xml"] = (
            HEAD + f'<p:sld {NS}><p:cSld><p:spTree>{GROUP}<p:pic><p:nvPicPr><p:cNvPr id="2" name="Page {number}"/>'
            '<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            '<p:blipFill><a:blip r:embed="rId2"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic></p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
        slide_rels = [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),
                      ("rId2", "image", f"../media/page{number}.png")]
        if notes is not None:
            slide_rels.append(("rId3", "notesSlide", f"../notesSlides/notesSlide{number}.xml"))
            types.append((f"/ppt/notesSlides/notesSlide{number}.xml", "presentationml.notesSlide+xml"))
            parts[f"ppt/notesSlides/notesSlide{number}.xml"] = (
                HEAD + f'<p:notes {NS}><p:cSld><p:spTree>{GROUP}'
                + placeholder(2, "Slide Image Placeholder", "sldImg", IMAGE_BOX)
                + placeholder(3, "Notes Placeholder", "body", NOTES_BOX, paragraphs(notes[number - 1]))
                + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')
            parts[f"ppt/notesSlides/_rels/notesSlide{number}.xml.rels"] = rels(
                ("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"),
                ("rId2", "slide", f"../slides/slide{number}.xml"))
        parts[f"ppt/slides/_rels/slide{number}.xml.rels"] = rels(*slide_rels)
    parts["ppt/presentation.xml"] = (
        HEAD + f'<p:presentation {NS}><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
        f'</p:sldMasterIdLst>{notes_master}<p:sldIdLst>{slide_ids}</p:sldIdLst>'
        f'<p:sldSz cx="{cx}" cy="{cy}"/><p:notesSz cx="{NOTES_SIZE[0]}" cy="{NOTES_SIZE[1]}"/></p:presentation>')
    parts["ppt/_rels/presentation.xml.rels"] = rels(*present_rels)
    parts["ppt/slideMasters/slideMaster1.xml"] = (
        HEAD + f'<p:sldMaster {NS}><p:cSld><p:spTree>{GROUP}</p:spTree></p:cSld>{CLRMAP}'
        '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>')
    parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = rels(
        ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", "theme", "../theme/theme1.xml"))
    parts["ppt/slideLayouts/slideLayout1.xml"] = (
        HEAD + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{GROUP}</p:spTree>'
        '</p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
    parts["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = rels(
        ("rId1", "slideMaster", "../slideMasters/slideMaster1.xml"))
    parts["ppt/theme/theme1.xml"] = THEME
    parts["_rels/.rels"] = rels(("rId1", "officeDocument", "ppt/presentation.xml"))
    parts["[Content_Types].xml"] = (
        HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
        + "".join(f'<Override PartName="{name}" ContentType="{CT}{kind}"/>' for name, kind in types) + '</Types>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", parts.pop("[Content_Types].xml"))
        for name, data in parts.items():
            archive.writestr(name, data)
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--notes", type=Path, help="the deck built with notes on a second screen to the right")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args(argv)
    for tool in ("mutool", "pdfinfo", "pdftotext"):
        if shutil.which(tool) is None:
            raise SystemExit(f"export_pptx needs {tool} (MuPDF for mutool, poppler for the others)")
    sizes = page_sizes(args.pdf)
    if len({(round(w), round(h)) for w, h in sizes}) != 1:
        raise SystemExit(f"{args.pdf} mixes page sizes; a deck has one slide size")
    notes = read_notes(args.notes, sizes) if args.notes else None
    with tempfile.TemporaryDirectory() as folder:
        images = render(args.pdf, Path(folder), args.dpi)
        if len(images) != len(sizes):
            raise SystemExit(f"mutool rendered {len(images)} pages, pdfinfo found {len(sizes)}")
        count = write_pptx(args.out, images, sizes[0], notes)
    noted = sum(1 for text in notes or [] if text.strip())
    print(f"wrote {args.out}: {count} slides, {noted} with speaker notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
