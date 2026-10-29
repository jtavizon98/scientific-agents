---
name: scientific-plotting
description: Design, iterate and review scientific figures and plotbooks (distribution, ratio and diagnostic plots) against the scientific contract and the reader's final-page tasks. Use when creating or revising plots for a report, thesis or plotbook, including figures embedded in reports.
---

# Scientific plotting

Read [plot production](references/plot-production.md). It owns the detailed
workflow and the statistical and display conventions.

[analyb](https://github.com/jtavizon98/analyb) is the supported default plotting
library: its style, labels, histogram comparison, saving and plotbook
composition are what this skill means by "the library's machinery". If you use
another library, follow [plotting-integration](../plotting-integration/SKILL.md)
to connect it to the same evidence and review steps, and read "the library" below
as your own.

1. Recover the reader task, the required evidence, the applicable reference
   artifacts, the actual imported library revision and the owning recipe or API.
   Keep coverage separate from page count. Record exact binning, normalization,
   ratios and uncertainties, plus the concrete acceptance features of the
   reference and the reasons for any departure from it.
2. Iterate at two scales: question, encoding, render, figure reading test; then
   coverage, grouping, composed pages, plotbook reading test. One can reopen the
   other. Plan candidate layouts, not an assumed one-shot final design. Give rows
   and columns explicit scientific roles, and test at final size whether overlays
   remove avoidable panels or page turns rather than following the rendering
   loop. Colors, line styles and markers remain available when they improve
   decoding. A study's grid, source split or denominator does not become a
   universal rule. See [design judgment examples](references/design-judgment.md).
3. Start from the equation: plot it as a function, or its terms as histograms.
   Prefer the field's standard plot forms (in high-energy physics, a
   distribution with ratio, pull or diagnostic panels below); a custom plot type
   must earn its place and say why. Label every axis (shared x once, each y),
   symbols before words. See "Design and iterate at two scales" in the procedure.
4. A plotbook is a collection of composed figure pages, read on its own. It
   holds plots, not long tables. If the reader sees it before the report, as
   recommended so the report's interpretation does not anchor the reading of the
   plots, each plot carries its legend and colour key, axis labels that name the
   compared quantities and, where the reading is not obvious, a short
   how-to-read note pointing to the report. See "What a plotbook holds" in the
   procedure, including what to show once results carry over to a second
   sample.
5. Use the library's plotting, labels, style, saving and composition machinery.
   Loading its fonts while rebuilding the renderer is insufficient. Identify the
   precise gap, then extend the library with a test rather than drawing around
   it. Preserve scientific semantics, signed and zero content, variances, flows
   and required covariance. Aggregate whole source bins before display
   normalization; never silently substitute automatic binning.
6. Prove uncertain and dense families using real data in actual page placement.
   Compact native cutflows show numeric values by default; verify their values
   and final-size legibility, using adjacent tables if needed. Audit scales
   across the complete affected inventory. Reserve label and legend space after
   all overlays and final axis transforms. Check glyphs, legend structure,
   data and error visibility and normal-size readability, not just clipping.
7. Run the render gate on the composed artifact through
   [render-review](../render-review/SKILL.md), with the applicable values,
   inventory and coverage inputs or bound equivalent evidence. Missing checks
   are not assessed; an unblocked lint result alone does not permit visual
   dispatch. A blank band over 25 % of a page's height fails the gate: recompose
   the page. Follow the [visual review protocol](../render-review/references/visual-review.md)
   and validate the bounded request with `review-preflight`. A substantial
   plotbook needs an economy image-capable independent reviewer for the residual
   reading tasks, with the reader brief and reference rasters before the
   author's verdict. Confirm actual pixel access; absent pixels mean not
   assessed. Require distinct reference-fidelity and reading-task findings.
   Contact sheets establish overview coverage, not text readability; inspect
   selected final pages and justified family representatives. Reuse accepted
   evidence, including moved unchanged pages; final status and repagination alone
   do not require all-page review. Record exact artifact and page evidence and
   resolve concrete failures. Validate numbers, inventory and navigation
   independently; a visual verdict cannot validate those.
8. Iterate within the confirmed contract until the reading tasks work and
   material defects are resolved. On presentation feedback, search the owning
   source and inventory for the same cause and inspect the affected families
   before patching the example; use the review protocol's bounded recheck rules.
   Escalate scientific choices, conflicting preferences and genuine readability
   conflicts. Settle the plotbook before the final companion prose and page
   routes, then verify and deliver the matched pair.

This skill does not authorize processing, scientific changes, uploads or source
publication. Recover existing agreements rather than asking the user to repeat
them.
