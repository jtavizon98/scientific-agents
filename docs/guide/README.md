# Working with agents on a scientific project: the handbook

A book for researchers who can use Git and write scientific code but are new to
coordinating agents. The skills in [`../../skills/`](../../skills/) are what the
agents read; this handbook explains to a person how the pieces fit, with the
decisions, evidence and handoffs of one working day. It is written as a LaTeX book
and is also the worked example of the
[report workflow](../../skills/report-writing/references/report-production.md):
citations go through biblatex and Biber with backreferences, every claim points
to a skill file and section, and the last chapter walks one small task through
the same checks.

Take what helps, change it for your project, and leave the rest.

## Chapters

| Chapter | Source | What it covers | Skills it points to |
| --- | --- | --- | --- |
| Essential terms | [terms.tex](chapters/terms.tex) | Vocabulary used throughout | |
| 1. Start and continue daily work | [daily.tex](chapters/daily.tex) | Choosing the result, owner and execution boundary, the work loop and its ending | [session-coordination](../../skills/session-coordination/SKILL.md) |
| 2. Investigate and settle decisions | [decisions.tex](chapters/decisions.tex) | Evidence base, the planning pass, carrying authorization with the action | [grilling](../../skills/grilling/SKILL.md) |
| 3. Develop and validate scientific code | [code.tex](chapters/code.tex) | Stage record, one owner per definition, tests that protect the claim, validation order, performance | [scientific-coding](../../skills/scientific-coding/SKILL.md) |
| 4. Produce and revise a report | [reports.tex](chapters/reports.tex) | Reader and knowledge, form, claim-level citations, figures and plotbook, review tracks, the exact PDF | [report-writing](../../skills/report-writing/SKILL.md), [scientific-plotting](../../skills/scientific-plotting/SKILL.md), [render-review](../../skills/render-review/SKILL.md), [source-library](../../skills/source-library/SKILL.md) |
| 5. Run, monitor and diagnose remote work | [remote.tex](chapters/remote.tex) | Preflight, parent contract, interpreting a handback, client loss | [long-job-continuation](../../skills/long-job-continuation/SKILL.md) |
| 6. Coordinate changes and hand them off | [handoff.tex](chapters/handoff.tex) | One writer per boundary, reviewing a contribution, durable source | [session-coordination](../../skills/session-coordination/SKILL.md) |
| 7. Recover and preserve work | [recovery.tex](chapters/recovery.tex) | Recovering context, outcome records, recovery sources, cleanup | [workspace-lifecycle](../../skills/workspace-lifecycle/SKILL.md), [unblocker](../../skills/unblocker/SKILL.md) |
| 8. Field checklists | [checklists.tex](chapters/checklists.tex) | One page each before work, before accepting, before handoff | |
| 9. Worked example | [example.tex](chapters/example.tex) | One small task from question to figure to report to review | [custom-plotting example](../../examples/custom-plotting/README.md) |
| 10. Make it yours | [yours.tex](chapters/yours.tex) | Starting small, a personal overlay, routing lessons, delegation, staying current | [scientific-mode](../../skills/scientific-mode/SKILL.md), [reflect](../../skills/reflect/SKILL.md), [correct](../../skills/correct/SKILL.md) |

A recommended reading habit: read the plotbook before the report, so that the
report's interpretation does not anchor your reading of the figures (the
Einstellung effect).

## Build

You need a TeX installation (`pdflatex`, `latexmk`, `biber`), a Python
environment with NumPy and Matplotlib, and `pdftotext` for the example. Run
everything from the repository root. Intermediates and the example output go to
`docs/guide/build/`; the PDF stays beside its source as `docs/guide/handbook.pdf`.
Git ignores both, so nothing generated is committed.

```bash
# 1. The worked-example figure (the output directory must not exist yet)
python examples/custom-plotting/render.py --renderer matplotlib --out docs/guide/build/custom

# 2. The handbook
(cd docs/guide && latexmk handbook.tex)
```

To rebuild the figure, delete `docs/guide/build/custom` first. Read
`docs/guide/build/handbook.log` and `docs/guide/build/handbook.blg` for warnings.

## Check

```bash
# Source check: bibliography keys, resources inside the library, formatting, raw quantities
python skills/report-writing/scripts/check_report_sources.py --root docs/guide --quantities \
  docs/guide/handbook.tex docs/guide/preamble.tex docs/guide/chapters/*.tex

# Render gate on the built PDF
mkdir -p docs/guide/build/session
cat > docs/guide/build/session/applicability.json <<'JSON'
{"checks": {
  "numbers": {"status": "not_applicable", "reason": "No measured results; the example figure has its own checks"},
  "inventory": {"status": "not_applicable", "reason": "Prose book with one example figure, no plotbook inventory"},
  "plan": {"status": "not_applicable", "reason": "No planned figure inventory"},
  "reuse": {"status": "not_applicable", "reason": "First edition; no prior acceptance"}
}}
JSON
python skills/render-review/scripts/render_gate.py gate --session docs/guide/build/session \
  --pdf docs/guide/handbook.pdf --log docs/guide/build/handbook.log \
  --blg docs/guide/build/handbook.blg --contract docs/guide/build/session/applicability.json \
  --out docs/guide/build/gate
```

`gate.json` in the output directory holds the verdict. A `fail` finding blocks
visual review until it is fixed or waived; see
[render-review](../../skills/render-review/references/workflow.md). A pass is
mechanical evidence, not a reading verdict.

The book class starts each chapter on a new page, so a chapter's last page and the
title page can carry a blank band taller than the default limit. Record each as an
exception: list `{"raster_sha256": ..., "page": ..., "reason": ...}` in
`docs/guide/build/session/blank-exceptions.json`, copying the hash from the finding in
`gate.json`, and pass `--blank-exceptions` to the next run. The exception lapses when that
page changes.

## Add a private layer

`preamble.tex` holds the packages and macros, and `\hook{name}` marks places where a
private handbook can add its own sections without editing these chapters. A private main
file sets `\newcommand{\guidehead}{...}`, `\input{preamble}`, defines
`\csname hook@name\endcsname` for the hooks it uses, and `\input{chapters/...}` the
public chapters. Put this directory on `TEXINPUTS` and `BIBINPUTS`, for example in
`latexmkrc` with `ensure_path('TEXINPUTS', "<path to docs/guide>//")`, and add
`\addbibresource{handbook.bib}` beside your own bibliography. The hooks are
`daily-continuation`, `reports-sources`, `reports-delivery`, `remote-hosts`,
`recovery-clients` and `recovery-backup`.
