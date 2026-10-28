# Render gate and review

Mechanical checks on a rendered PDF before visual review. The gate finds
clipped or overlapping text, small type, unresolved figures, build errors,
missing printed values, misplaced panels and half-empty pages, so reviewer effort goes to the
reading tasks declared in the review request. A pass does not certify reading-task
success or reference fidelity, and the gate has no combined score.

## Command

Run it on every candidate PDF before dispatching visual review:

```bash
python3 scripts/render_gate.py gate --session <session dir> \
  --pdf <pdf> --log <tex log> [--blg <blg>] [--values <manifest>] \
  [--pagemap <map> [--plan <plan>]] \
  [--previous-manifest <old packet/manifest.json> --reviewed <reviewed.json>] \
  --contract <applicability.json> \
  [--blank-exceptions <exceptions.json>] [--max-blank-band <fraction>] \
  [--approver <approval identity>] \
  --out <new dir>
```

It binds every input by SHA-256, including registered value-source files, and
rechecks the bindings after all checks. It writes `gate.json`, the lint report,
and the review packet (`page-NNN.png`, labelled contact sheets, `manifest.json`).
Numbers, inventory and diff reports are written only when their corresponding
inputs are supplied. `lint-pdf`, `packet`, `diff`, `numbers` and `inventory` run
the parts alone; `--help` documents each check. Figures named in the PDF must
resolve on disk. The `lint-pdf` command owns
`--no-figure-check`, which explicitly records skipped figure checks; `gate`
always checks source figures and does not accept that flag.

## Coverage and visual dispatch

`blocked` means an unwaived failure was detected. `ready_for_review` additionally
requires disposition of all optional checks: `build`, `bibliography`, `numbers`,
`inventory`, `plan`, `reuse`. A supplied input runs its check. Without one, the
check is `not_assessed` unless `--contract` explains why it is `not_applicable`,
or supplies PDF-specific, hash-bound equivalent `external` evidence. Lint-only
runs remain useful diagnostics but do not authorize model dispatch. Gate exit
status reports detected failures; always use preflight for dispatch readiness.

Example contract for a prose-only first edition (adapt reasons, never copy them
onto a numerical plotbook):

```json
{"checks": {
  "bibliography": {"status": "not_applicable", "reason": "No bibliography in this memo"},
  "numbers": {"status": "not_applicable", "reason": "No reported numerical results"},
  "inventory": {"status": "not_applicable", "reason": "Prose-only memo, no figures"},
  "plan": {"status": "not_applicable", "reason": "No planned figure inventory"},
  "reuse": {"status": "not_applicable", "reason": "First edition; no prior acceptance"}
}}
```

Here `--log` supplies the build check. An external disposition needs `status:
"external"`, a specific `reason`, absolute `path`, that file's `sha256` and the
candidate's `pdf_sha256`. The owner must inspect that evidence and its scope;
hash validation is not semantic approval. Use this for existing custom-composer
inventory/navigation checks rather than inventing a second implementation or
declaring unsupported page maps irrelevant. A revised artifact with available
prior evidence must use `reuse` inputs or explain bound equivalent reuse evidence.

Before each visual dispatch:

```bash
python3 scripts/render_gate.py review-preflight \
  --gate <gate.json> --request <visual-request.json> --json <preflight.json>
```

The request binds `gate_sha256` and declares `model`, `effort` (or honest inherited
visibility), `cost_tier` (`economy` or `escalated`), `route_reason`, `pages`,
`reading_tasks`, and `stop_condition`. Each candidate page must be selected or
belong to a justified family with `pages`, selected `samples`, and `reason`.
The complete raster packet is coverage evidence, not an instruction to send all
images to a model. Example family: `{"pages":[1,2,3,4],"samples":[1,4],"reason":
"Same layout; samples cover longest labels and signed tails; full geometry passed"}`.

The preflight rechecks artifact/input/output hashes and packet pixels, rejects
incomplete coverage and unaccounted candidates, and requires `escalation_reason`
for expensive routes. Opus/Astra cannot be labelled economy. Selecting more than
12 pages additionally requires `scope_reason`, including near-exhaustive requests; this is
an escalation checkpoint, not a recommended batch size. Reasons must name an
actual unresolved problem, not final status or page-count change. Report selected
coverage honestly; sampling does not create an individual verdict for unseen pages.
Each family containing candidate pages must sample a candidate, not only an
unchanged carried page. Diff localization boxes are omitted after page-count
changes because positional pairing would compare unrelated content.

Preflight is an explicit executable check. It does not intercept arbitrary native
or shell model calls; callers are required to invoke it. Automatic model pricing,
semantic validation of reasons and provider quota enforcement are not implemented.

## Rules

- **Blocking.** A `fail` finding blocks dispatch to visual review until it is
  fixed or waived. A waiver is an entry in `<session>/waivers.json`
  (`id`, `check`, the finding's `fingerprint` from `gate.json`, `pdf_sha256`
  or `figure_sha256` of the checked version, `reason`, `approved_by`). A
  finding carrying `figure` requires that figure's `figure_sha256`; only
  composed-PDF findings accept `pdf_sha256`. It covers that one finding in
  that one version; a changed artifact or a fingerprint matching nothing leaves
  it unmatched. When `waivers.json` exists (even if empty or malformed), the
  gate requires an explicit `--approver` identity and otherwise stops before
  checks or output creation. It applies a waiver only when `approved_by`
  exactly matches that identity and `STATE.md` records approval on one line:
  `waiver <id>: <reason> (approved by <identity>, <YYYY-MM-DD>)`, with the same
  id and reason. Identities are nonempty single-line strings without surrounding
  whitespace, commas or parentheses. The gate records the selected identity and
  hashes the waiver and state evidence. Preflight rechecks the state hash when
  any waiver was applied; approval withdrawal requires a new gate run. This is
  an evidence record, not identity authentication or authorization to approve.
  The caller must select an authorized approver under the project's policy. Flags,
  including density (`panel-narrow` under 4 cm, `page-underused` under 50 %
  of the content frame inferred across the pages, or of the page inset by
  12 mm for documents under three pages), are advisory and go to the reviewer as pointers.
- **Whitespace.** The default layout policy rejects large empty bands.
  Each page is rasterized in grey at 36 dpi; the tallest run of
  ink-free rows across the density frame, as a fraction of the page height, is
  `density.pages[].blank_band`. Above 0.25 it is a `page-blank-band` fail. The
  final page is measured but not checked. Fix the page first: recompose, regroup or
  enlarge. Where a band is necessary (for example a book-class title page or
  chapter end), record the exception in `<session>/blank-exceptions.json`
  (`[{raster_sha256, page, reason}]`, the hash copied from the finding; `page`
  is a note for readers) and pass it with `--blank-exceptions`. The finding then
  becomes `info` with the reason. The exception lapses when that page's raster
  changes, a new page number included; one matching no page is flagged.
  Blank-band exceptions do not use the waiver approval mechanism, but each one is listed in `gate.json`
  and the session folder, and visual review sees the page. Change
  `--max-blank-band` only for a reason recorded in `STATE.md`. The advisory `page-underused` flag counts
  placed figure boxes as used and misses blank space inside or below them.
- **Fonts.** Text under 5 pt at final placement fails; under 7 pt is flagged.
  Comparisons allow 0.05 pt tolerance for TeX-to-PDF point conversion. Short
  classified sub/superscripts fail under 3.5 pt, flag between 3.5 and 5 pt,
  and skip the 7 pt advisory tier. A script exemption requires known ownership
  by the same text object as its base. Type 3 glyph visibility requires
  nonzero-alpha painting inside that glyph's procedure; unrelated page paths
  and invisible render-mode text do not establish visibility.
- **Carry-over.** A page keeps an earlier verdict only when its raster at the
  same DPI is identical to a page listed in `reviewed.json`
  (`[{raster_sha256, verdict_ref}]`). Match identical rasters across page movement
  and count changes. Changed pages and neighbours are review candidates, not a
  mandatory exhaustive model assignment. Contact sheets cover the whole book.
  Verify page order, numbering and routes separately, including deletion or
  movement of unchanged pages. Footer changes do not carry automatically: use
  bound composition/body-placement evidence and a bounded family recheck, without
  silently masking pixels or claiming exact full-page identity. Final status
  does not reopen accepted appearance evidence.
- **Printed values and inventory.** `--values` checks each number recorded by
  `analyb.printed` against the PDF text; `--pagemap` checks each page's
  figures, headings and captions against
  `write_compact_plotbook(page_map=True)`. Maps must number pages exactly
  `1..page_count` in order and use the producer's consecutive two-column
  row/column slots. Inventory checks physical placement and exact heading
  and caption text in their intended regions, excluding figure-internal
  text; each caption must belong to its own figure. Value pages must be
   positive integers or null, and non-null source references must be registered.
   The gate pins analyb's schema and matching rule v4: unary signs, decimal
   digits, grouping, exponents and supported suffixes are checked as complete
   tokens. Unsupported or ambiguous numeric candidates fail closed. Context
   identifies the extracted row; column assignment and arithmetic are not
   checked. Blank value text and invalid context labels produce blocking
   `values-invalid` findings rather than aborting report generation.

For documents of three or more pages, the inferred density frame can hide
uniformly sparse content: identical small panels on every page can fill that
inferred frame and escape `page-underused`. Detecting that case requires an
independently declared frame. This advisory limitation does not affect the
12 mm inset fallback for shorter documents.

## Producer side

analyb's `check_figure` and `set_figure_check("warn" | "raise")` lint each
figure at save time and write a `<stem>.figcheck.json` sidecar that the gate
imports; `analyb.palette` reports colour distances under simulated colour
vision as diagnostics. The tool does not import analyb; compatible producers
can emit the same schemas (`analyb.figcheck` v1, `analyb.printed_values` v4,
`analyb.plotbook_page_map` v1). The exact value matching rule is pinned in
`scripts/render_gate.py` and checked against each manifest.

## Dependencies and policy tuning

Run from this repository with Python 3.10 or newer. Runtime tools are MuPDF's
`mutool` (including `mutool run`), Poppler's `pdffonts`, `pdftotext`,
`pdftoppm`, plus Python Pillow. Matplotlib, pytest, and a LaTeX
installation with `pdflatex`, `fontenc`, `lmodern`, `graphicx` and `geometry`
support the synthetic tests. No private artifacts or network services are needed.
Tests skip dependency-specific cases when their declared tools are absent;
inspect pytest's skip report rather than treating a partially skipped run as
full render validation.

Font size, blank-band size, panel width and page utilization are readability
policies, not proofs of scientific correctness. Defaults remain 5/7 pt for
blocking/advisory fonts, 0.25 for blank bands, 4 cm for panel width, and 50%
for utilization. `lint-pdf` exposes `--min-font-pt`, `--flag-font-pt` and
`--max-blank-band`; `gate` exposes the blank-band threshold and retains default
font floors. Panel/utilization thresholds are module constants, not CLI options.
Record reasons for policy changes and raster exceptions in session evidence.
Changing a stylistic threshold does not relax hash/schema validation, token
matching, figure resolution, clipping, overlap or inventory checks. Printed
value matching verifies transcription, not arithmetic, column assignment or
physics; visual review and domain review remain separate.

By default the gate runs lint (including source-figure checks) and a complete
raster packet. Optional checks without inputs are `not_assessed`, not passed
or silently skipped; only reasoned applicability or bound external evidence
completes their coverage. Without a previous reviewed manifest, every page is
a review candidate. `lint-pdf --no-figure-check` is an explicitly recorded
diagnostic skip, unavailable on `gate`. The final-page blank-band exemption
is automatic; it does not exempt that page from other checks or visual review.

## Verification

```bash
<python> -m pytest tests/test_render_gate.py -q -rs
```
