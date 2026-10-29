# One source, two reports

This synthetic example demonstrates shared source identity, section pinpoints,
linked citations and bibliography backreferences. It makes no research claim.
The source is the authored local `source.md`; its bibliography entry is owned
once in `bib/workspace.bib` and loaded by both reports.

Requirements: pdfLaTeX, biblatex/Biber, hyperref, geometry, fontenc, lmodern and latexmk.
From this directory:

```bash
python ../../skills/source-library/scripts/check_bibliography.py bib/workspace.bib
latexmk -pdf -interaction=nonstopmode -halt-on-error report.tex followup.tex
```

Check the logs for missing/duplicate keys and rerun requests. In each PDF follow
the blue citation to the entry and its backreference to the citing page. The
source section locator is printed beside the claim, not stored as publication
extent in the bibliography. Read `source.md` to verify the cited statement.

To exercise maintenance, correct the shared entry's descriptive title and rebuild
both reports. Do not copy the entry into either `.tex` file. A substantive new
edition would need a separate identity if either report still cites version 1.

Generated outputs are ignored. A successful build checks citation wiring, not
the truth of an arbitrary source or a user's scientific conclusions.
