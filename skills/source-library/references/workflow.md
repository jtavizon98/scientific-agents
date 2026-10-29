# Shared sources and report citations

One source should have one owning entry and a stable identity across maintained
reports. This prevents corrections to an author, edition or DOI from being lost
in report-local copies. Use the project's existing library; the layout below is
an example, not an installation requirement:

```text
bib/
  literature.bib       # papers, manuals, documentation, software releases
  workspace.bib        # maintained project guides and reusable references
  studies/             # independently citable evidence, grouped by topic
```

## Register the source you actually inspected

Record checked author/organization, title, source date, edition/version, DOI or
stable URL, and access restrictions. Inspection date is a different field from
publication date. For local evidence record the portable path and exact inspected
revision or artifact identity. A dirty working copy is not its base Git commit.

Keep existing descriptive keys. A useful convention for new local records is
`work:<description>` for maintained references and `study:<date>:<description>`
for dated evidence. Keys and optional descriptive shorthands are unique across
the entire library. Moving an entry between files does not change its identity.

An updated live document and an explicitly cited historical edition may require
separate entries. Never silently retarget a historical citation to newer inputs
or a rerun. Bibliography inclusion means neither approval of its claims nor
permission to redistribute the source.

## Cite the claim, not just the subject

Place the citation where a reader needs to check the statement. Include a
printed page, named section, equation, figure, table or code path at a revision.
Use the document's printed pagination, which can differ from the viewer index.
The bibliography's `pages` field describes publication extent, not the passage
supporting your claim. Grouped citations need a separate locator for each source.

```latex
\cite[p.~23, sec.~3.9]{source-key}
\cites[eq.~4]{method-key}[table~2]{input-key}
```

These are syntax examples, not verified source locators. Distinguish a source
supplying the method from one supplying inputs. Tables, captions and reproduced
panels need the same provenance. Reconcile conflicting sources explicitly; a
newer date does not automatically make a source authoritative for every claim.

Register independently citable evidence collections, not every log or session
record. Keep member hashes and configurations in their manifest and cite the
specific member/section alongside the claim. Session narratives can point to
evidence but should not replace an available primary source.

## Build and check

The supplied [bibliography preflight](../scripts/check_bibliography.py) checks
explicitly named library files without changing them:

```bash
python <skill>/scripts/check_bibliography.py path/to/literature.bib path/to/workspace.bib
```

It requires Biber and fails on parser warnings, duplicate keys and duplicate
nonempty shorthands across the selected files. Files parse independently: define
custom string macros in each file that uses them, or use your report's real
combined Biber build for libraries that deliberately share macro definitions.
This preflight does not check cited-key resolution, metadata accuracy, claim
support or omitted library files. Use the actual report build and source review
for those checks. No filenames means a usage error, not an empty passing audit.

For new LaTeX reports the [two-report example](https://github.com/jtavizon98/scientific-agents/blob/main/examples/citations/README.md)
uses biblatex/Biber, linked citations
and `backref=true`. Load the shared resources with `\addbibresource`; avoid
duplicating entries into each report. Blue links are a readable default, not a
scientific requirement. Build using pdfLaTeX, Biber and two further pdfLaTeX
passes, or a verified latexmk equivalent.

Check duplicate keys/shorthands, missing citations, malformed metadata, unresolved
references and rerun requests. Inspect both claim-to-entry links and bibliography
backreferences in the built artifact. A backreference points to this report's
citing page; it is not a locator inside the cited source. A clean build proves
neither metadata accuracy nor claim support; inspect those separately.

Keep `.bib` source under version control. Generated `.bbl`, `.bcf`, `.blg` and
PDF outputs follow the project's artifact policy. A required submission `.bbl`
is an explicit delivery item. Local PDFs and full-text extractions remain a
separate reading layer unless redistribution is permitted.
