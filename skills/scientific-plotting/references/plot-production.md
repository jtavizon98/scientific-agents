# Plot production

Use the [scientific-plotting skill](../SKILL.md) for scientific plots and
plotbooks, including figures embedded in reports. The plotting library owns
reusable drawing, style, histogram comparison, saving and plotbook machinery.
Analysis recipes own sample identities, scientific definitions, mappings and
display choices. Report formatting must not replace the agreed scientific figure
style.

## Recover the applicable agreement

Before editing, inspect the current recipe, the actual imported library checkout
and revision, the library's README and cheatsheet, the accepted plotbook and its
generating source. Resolve checkouts from the current environment; historical
paths and refs are evidence locators, not instructions to switch versions.

Record a concise plot contract in the task's existing state or decision record:
reference artifact and recipe; plot family; exact target edges and ranges; counts
versus density and raw versus normalized shape; numerator, denominator and
uncertainty convention; palette and normalization; panel and page layout.
Extract concrete acceptance features from the applicable reference and recipe:
axis wording and units, justified branding, source and flavour encodings, legend
structure and page orientation. Record deliberate departures and their reasons
before rendering; check them against the user-fixed requirements. A reference
is an acceptance baseline, not merely visual inspiration. Keep these features
in the existing plot contract rather than a separate checklist.
Distinguish scientific invariants, explicitly user-fixed presentation
requirements, and provisional inherited design choices. An inherited recipe or
page grid is a starting point unless the applicable decision fixes it. Ordinary
regrouping and encoding trials within those constraints do not need another
approval round. Resolve these from the latest applicable user decisions. Ask
only about a material conflict that the records cannot resolve. Do not copy a
historical choice from another plot family just because its screenshot looks
similar.

If polished example plots exist, inspect them. Their appearance does not
authorize copying their datasets, luminosity, statistical assumptions or axes
into a new comparison.

## Design and iterate at two scales

Start from the equation. Write each plotted quantity as an equation (numbered in
the report, or in the plot's how-to-read note) and plot the equation as a
function or its terms as histograms, using the equation's symbols in labels and
legends. Default to the standard HEP grammar: a distribution with extra panels
(ratio, pull, a diagnostic such as the stacked terms of a bin decomposition).
Each new plot type costs the reader learning time, so a custom type must earn
its place: use it only when the standard form cannot carry the message, and say
why in its how-to-read note. Every axis carries a label: a shared x axis once,
under the lowest panel; each panel its own y label. Prefer the mathematical
expression to words, except where a name is clearer (an observable such as
"Second b-jet $\phi$"). These are recommendations, not laws.

Before choosing a renderer, name the reader's task and the measurements needed
to perform it. Record coverage separately from page count: dense means useful
comparisons per page, not fewer observables. For an audit, map each material
requirement to its definition, available raw and weighted stages, cut-matched
distribution, conditional change and newly admitted population where relevant.
Mark missing evidence explicitly. A catalogue of existing histograms is not by
itself an adequate coverage plan.

Decide a plotbook's coverage after the scientific answer is agreed: plots exist
to answer the question, not to list every artifact a study produced.

Plan plausible comparison groups, not a one-shot final layout. Use two connected
loops; page review may reopen figure design:

1. **Figure:** question, encoding, actual-data render, reading test, revision.
   Name the reference, baseline and alternatives; identify what is held fixed.
   Keep one observable per ordinary distribution plot. Choose which comparison
   dimension belongs in an overlay and which needs separate panels. Colors,
   line styles and marker shapes are tools, not mandatory or forbidden encodings.
   Test whether they remain distinguishable where curves meet and at final size.
   Organize legends by the comparison's structure, with stable ordering and glyphs
   matching the actual series. Avoid shrinking or moving labels out of their
   established positions just to accommodate an untested overlay.
2. **Plotbook:** coverage, grouping and sequence, composed pages, reading test,
   revision. Assign meanings to rows, columns and pages. Put comparisons together
   when simultaneous viewing helps; separate them when the overlay obscures the
   effect. Preserve corresponding layouts for related views. Keep ordered stages
   in a consistent reading direction and comparison groups intact across breaks.
   Remove redundant pages, not unique evidence. An underused page and tiny plots
   can coexist: reconsider composition rather than merely shrinking or enlarging
   everything. No universal 2x3 grid, source split or flavour overlay is required.

Read the [design judgment examples](design-judgment.md) for annotated
before/after decisions. Recover the reasoning, not the particular layout.

Prototype the densest or least certain group using retained real data, including
its captions and final page placement. Test whether an overlay can remove
avoidable panels or page turns while preserving readable series and errors;
do not let the rendering loop determine one page or panel per flavour or source.
Make row and column roles explicit in the composed page. Record the selected
encoding and reading-size evidence; compare alternative layouts only when a
concrete tradeoff remains. Agents normally choose and iterate autonomously within
the confirmed scientific and display contract. For an unresolved scientific
choice, a conflicting preference or a material readability conflict, take the
best-supported default, record it and keep going
([decide, record, report](../../session-coordination/references/consequential-actions.md#decide-record-report));
ask first only when no default is defensible or the choice changes what the
figure is for. Changing a ratio reference can change the
scientific comparison; it is not merely a layout repair.

### What a plotbook holds

A plotbook that is read before the report, for a first impression, must be
readable without the report; the report holds derivations and the plotbook
points to them. Reading the plotbook first is a recommendation: the report's
interpretation then does not anchor how the plots are read.

- A plotbook holds plots. Long tables, such as a per-event weight longtable, do
  not belong in it; a small selected table may.
- A page with a large empty area is a rejection reason. The render gate fails a
  blank band taller than 25 % of the page height (`page-blank-band`); recompose
  the page or record a justified exception as the
  [render gate procedure](../../render-review/references/workflow.md) describes.
- Once results transfer between validation cohorts, show the development cohort
  plus one transfer-check summary; side-by-side cohorts are not a default.
- Settled presentations may be retired once superseded; the dated revisions keep
  the history.

## Reuse the implementation

Consult the library's current public plotting API and the accepted recipe first.
For analyb the implementation owners include `analyb/style.py`,
`styles/analyb.mplstyle`, `colors.py`, `config.py`, and the plotting and
plotbook modules. Reuse the suitable public helper and existing registration
path. Importing the library solely to apply fonts while recreating its panels,
uncertainty rendering and PdfPages infrastructure independently does not satisfy
this rule.

When the API lacks a required capability, identify the precise gap. If you
maintain the library or your own fork, extend it whenever a reusable capability
is missing, with a test and a cheatsheet entry, rather than drawing around it in
a recipe; otherwise propose the change to the maintainer. A thin task adapter
over existing primitives is for genuinely task-specific glue. Do not silently
substitute a generic data/MC helper for a different statistical contract or
rewrite a renderer to avoid inspecting the API.

## Established appearance

These describe the analyb style and the conventions that worked. Adapt them to
the library and the applicable recipe.

- Use the library's serif/STIX MathText style, inward ticks, appropriate minor
  ticks, compact legend and reserved label space. Preserve sample-to-color roles
  from the applicable recipe, not Matplotlib's default cycling.
- Use a shared x-axis with the ratio panel underneath for established 1D
  comparison families; preserve their relative panel sizes and ratio limits.
  A side-by-side ratio axis is not the accepted substitute.
- Plots stand mostly on their own. The legend and colour key sit inside the
  plot. Axis labels state the compared quantity with the stages substituted,
  e.g. (N_B - N_A)/N_A, so no title or separate key is needed. Avoid in-figure
  titles for ordinary 1D histograms; use the notation of the note or paper,
  disambiguate object rank where necessary, and give actual units. A plotbook
  page has no explanation block at its top. A plot whose reading is not obvious
  carries a short how-to-read note next to it that points to the report section
  or numbered equation explaining it. Define every task-specific term in the plot
  or its note: "median absolute residual" without its definition fails.
- Use the library's heatmap helper for intensity heatmaps. For differences or
  ratios needing a diverging map, pass the actual colormap object, not a string
  that can select an unrelated Matplotlib builtin of the same name. Differences
  center on zero, ratios on one.
- Comparable input heatmaps share a meaningful color domain. Clean heatmaps
  have no axis grid or mesh seams. Retain true bin geometry, including
  nonuniform edges; preserve response orientation and mask undefined cells.
- Use existing plotbook composition; start with the applicable family-specific
  page grid and revise it through the design loops unless explicitly fixed.
  Do not substitute the report's custom layout for the accepted plotbook.
  Keep identity captions concise in a diagnostic plotbook.

These conventions govern presentation. A log scale must not hide signed content,
and labels such as ATLAS Internal, energy, or luminosity must be justified by
the actual comparison. An old example's label is not evidence for a new one.

## Binning and statistical meaning

Recover exact agreed display edges from the prior recipe or configuration, not
from guessed visual spacing. Input histogram edges and agreed display bins can
differ. Aggregate whole source bins before normalization, retaining sums,
sumw2, flows, and covariance information needed for the requested statistic.
Keep fine-grid evidence and previous artifacts intact. Do not interpolate,
split weighted bins, feed histogram centers to raw-sample binning rules, or
silently choose automatic bins when an agreement exists.

Counts, counts per width, and unit-area density are distinct quantities.
Labels and normalization must describe the actual transformed values. Compare
the appropriate sums or width integrals when verifying a display change.
Let the library format histogram y labels after whole-bin aggregation and
density transforms; do not rename them ad hoc. Weighted event cutflows use
Events, Survival (own first displayed stage) and Cut efficiency (own previous
stage). Distinguish Raw events from Raw objects; nonsequential object-bin
quotients are not event survival or efficiency. State denominators and weight
mode in captions. Retain native labels and readable weighted values when
self-contained cutflows are requested. For compact native cutflow bar charts,
show a value beside each bar by default: integer counts for raw entries and
consistently formatted signed yields for weighted entries. State any rounding or
common scale. Verify values against the plotted data and inspect labels at final
page size, including their clearance from errors and branding. If values do not
fit readably, revise the composition or supply an adjacent value table rather
than silently omitting them. This is a cutflow convention, not a requirement to
label every histogram bin.
Unknown stored variance is unknown, not permission for Poisson errors or invented
bands. Nested stages with common event weights require the appropriate subset
covariance.

Where the contract calls for reference unity points, draw them with available
relative errors in every applicable ratio panel, including non-lepton families.
A band alone is not equivalent. Suppress undefined zero-reference bins rather
than drawing false unity. When a pseudodata or model role is a drawing role,
preserve the underlying arithmetic, weighted variances and undefined
denominators; keep independent combined errors in their separate diagnostics and
do not mix the two presentations.

Paired weight-mode and retained/removed comparisons may require covariance.
Preserve the current accepted statistical contract even while restoring an
earlier appearance. A data/MC convenience helper can mask negative denominators,
rebin, or change error propagation; choose it only when those semantics apply.
Do not replace zero-reference ratios with unity or clip inconvenient values
without a visible indication.

Same-event comparisons (two processings of the same simulated events, e.g. the
stages of a chain) default to this ratio presentation unless a study's accepted
contract says otherwise: draw the ratio the way its curve is drawn in the main
panel (a line stays a line), with the paired error
sigma_q^2 = sum_i (v_i - q b_i)^2 / B^2 as its only band, where, in each bin, v_i and b_i are
event i's weights in the two processings (zero where the event does not enter
that bin in one of them), V = sum_i v_i, B = sum_i b_i and q = V/B.

This is the first-order (delta-method) statistical variance of the ratio, with
the covariance of the shared events kept. It assumes independent events, each
contributing a fixed pair (v_i, b_i); correlated events must be grouped into
their independent unit first. It needs B well away from zero, and it does not
include uncertainty in the weights themselves or in a shared normalization;
those need their own propagation. As checks, identical processings give zero,
and an unweighted subset (B = N, V = k) gives the binomial q(1-q)/N.

Per-arm independent errors differ from it by 2q sum_i v_i b_i / B^2: they
overstate the uncertainty when the shared contributions are positively
correlated, the usual case for nonnegative weights, and understate it when
negative weights make the correlation negative. Either way they answer a
different question, so do not draw them beside the paired band. State the
formula in the caption or the how-to-read note.

### Scales and final geometry

Audit the complete affected inventory for scale choice, not just observables
mentioned as examples in feedback. Inspect displayed values and error envelopes.
Use linear scales when differences near a common value matter; consider log for
wide positive ranges. A log scale must not hide zero or signed support or lower
uncertainty endpoints. A labelled zero-preserving symlog can be useful when a
reading-size comparison demonstrates its benefit; it is not an automatic
fallback.

Unless a more specific range is agreed, a ratio axis is linear and symmetric
about one and chosen so the bulk of the bins' fluctuations are readable. A range
stretched to the most extreme bin squeezes the populated bins onto unity and can
overstate agreement. Set the half-width from a high quantile (0.9 by default) of
|ratio - 1| plus its comparison error over populated bins (reference error at
most 0.25), add modest padding, round up to a readable value and cap it at
[0, 2]. Use normalized values for shape views. Share the range within comparable
groups (cohorts, channels) and record any scientifically justified exception.
Ratios beyond the range need a visible edge marker and a per-panel off-scale
count in the caption or key; error bars and bands may run off the axis. Do not
impose a universal 0.5-1.5 range, truncate errors to enable log, or clip without
that indication. Draw a full-range view in addition only where a study asks for
it.

Apply data and error bounds and annotation headroom after all overlays and final
axis scales, then draw and inspect. A later set_ylim can undo earlier clearance.
Use the library's headroom and artist-bounds helpers (analyb's
`reserve_annotation_headroom` with the exact plotted envelope, and
`artist_axes_bounds` for explicit label and legend measurements, when the
imported revision provides them; see its cheatsheet for ordering and
limitations). A no-change return is not a clearance certificate. Headroom in
log and symlog axes must be measured in transformed space.
Geometry checks can flag legends outside axes or data beneath annotation regions;
they cannot certify readability or decide the best encoding. Enable the
library's figure check while iterating and run the render gate
([render-review](../../render-review/SKILL.md)) on each composed PDF before
visual review.

## Render and accept

Before batch rendering, prove representative members of every affected family
in their composed pages: densest legend, long labels, long tails, signed, zero or
undefined content, nonuniform bins, complex cutflow and largest captions where
present. Record intended physical page or figure size and normal viewing
conditions. A large standalone image is not proof that six reduced copies are
readable.

Use the [reading-task review protocol](../../render-review/references/visual-review.md).
For a substantial plotbook obtain bounded independent visual review of selected
final rasterized pages, with the reader brief and relevant reference rasters
before the author's verdict. Require separate findings on reference fidelity and
reading-task success; numerical correctness or absence of clipping does not
establish either. Verify image access using the review protocol before accepting
visual findings. Programmatic checks cover the complete inventory, geometry,
printed values and navigation where applicable. Validate their coverage and the
explicit economy visual route with the render gate's `review-preflight`. Contact
sheets provide overview; selected pages at reading size test representative
family layouts, new or changed encodings and relevant flags, with enlarged crops
for ambiguous defects. Phone fit-page thumbnails alone cannot pass small-text
readability. Record page numbers, render sizes, findings and exact PDF identity;
do not claim vision read a PDF.

Verify numerical preservation, whole-bin transforms, panel inventory, page
groups, printed pagination and report routes separately. Fix demonstrated
mechanical bugs in the owning helper and retain focused regressions. Re-render
changed and adjacent pages; verify navigation after repagination and affected
family representatives after global styling or scales change. Preserve accepted
evidence for untouched families; do not claim fresh inspection of unsampled
pages. Final delivery does not require another exhaustive visual pass.

Stop when the reader tasks succeed, required evidence is present and material
defects are resolved. Neither a prescribed iteration count nor speculative
cosmetic churn is required. Unresolved failures block technical handback; record
the specific conflict rather than replacing review with a generic PASS.

Settle the plotbook's structure and evidence and page map before final companion
prose and navigation. Update embedded figures and rebuild affected reports (see
[report-writing](../../report-writing/SKILL.md)). If writing exposes a missing
comparison, reopen the plotbook loop and revalidate affected claims and routes
before delivering the pair.

A plot-only correction should consume retained outputs. If the requested display
cannot be reconstructed from them, name the exact missing artifact before
proposing more processing. Preserve previous outputs and hand back the
regenerated paths, recipe and version, reference contract, validation, and
remaining deviations. Rendering success alone does not establish style fidelity.
