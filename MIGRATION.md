# Migration status

Status: all fourteen skills extracted from the author's thesis workflow; the
author's live setup uses this repository. Client discovery and the OpenCode
wait plugin are not yet verified in fresh sessions.

The intended audience knows Git and basic scientific coding, but need not know
agent tools, review-evidence formats or the original thesis. The handbook is a
new explanation for that audience, not a copy of private session history.

## Contents

- Fourteen skills in a flat `skills/<name>/` layout with `references/` and
  `scripts/`, and a Claude Code / Codex plugin manifest.
- Render gate and visual-review preflight, report-source and bibliography
  checks, job monitor and wait, and workspace sweep, each with tests.
- Matplotlib and public-analyb plotting examples and a two-report citation
  example, with explicit evidence contracts.
- The handbook as LaTeX chapters (`docs/guide/`), with a worked example built
  from the plotting example. Projects can `\input` its preamble and chapters
  and add their own.

## Checked

- 206 tests and 126 subtests pass with Python 3.13.
- The handbook builds with pdfLaTeX and Biber (41 pages); the render gate has no
  blocking finding; an image-capable reviewer read selected pages and its
  findings were fixed.
- An independent copy and numerical review (different model family) found no
  private leaks. Its setup, consistency and wording findings were fixed; the
  paired-ratio uncertainty text now states its assumptions.
- Upstream licences and pinned commits for grilling, wizard and unslop match
  their sources. Relative Markdown links resolve.

## Not yet verified

- Skill discovery in fresh Codex, Claude Code and OpenCode sessions.
- The OpenCode `monitor_wait` plugin outside the author's setup.
- A connected scientific study using every skill end to end.
- Human review of the handbook.

Documentation describes intended use; it does not claim all paths have been
runtime-tested.
