# Minimal report template

`report.tex` is a template for a memo or short article. Edit the metadata
commands and the section content. It uses common pdfLaTeX packages, siunitx and
biblatex with the Biber backend, and keeps evidence and provenance visible
without imposing a large structure.

It defines the headline and choice boxes and the status macros that
[../report-production.md](../report-production.md) refers to. The palette is
Catppuccin Latte. Each status macro carries a text label and a symbol because
colour alone is not reliable in print or for readers with colour-vision
deficiencies. Keep that convention when you add states.

Before copying it, define the audience and question and choose memo, article or
book by scope, as described in the procedure. A substantial report with
dependent chapters, front matter or reference appendices should start from an
outline suited to that structure, not accumulate sections here.

Adjust the `\addbibresource` path to your shared bibliography library. Do not
create a report-local copy of a source. Use `\SI` for quantities (it avoids the
`\qty` delimiter-sizing clash with the physics package), plus `\num`, `\unit`,
`\SIrange` and `\numrange`. Run the source-format and quantity checks in
`../../scripts/check_report_sources.py`, then build with `pdflatex`, `biber` and
two more `pdflatex` passes, and inspect the logs and the rendered pages.
