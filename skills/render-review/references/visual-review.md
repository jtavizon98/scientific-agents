# Reading-task review

This protocol supports [plot production](../../scientific-plotting/references/plot-production.md)
and [report writing](../../report-writing/SKILL.md). It tests whether the
intended reader can use the artifact. Numerical, source and scientific review
remain separate.

## Mechanical coverage, residual visual review

Run the render gate and account for every applicable check before dispatch.
Numbers, inventory, navigation and geometry belong in programmatic checks or
hash-bound equivalent evidence. A missing check is not assessed, even if lint
passed. Visual review concentrates on remaining uncertainty: readable encodings,
occlusion, contrast, useful comparison and final-size comprehension. It does not
repeat the full mechanical audit or certify scientific correctness.

Use an economy image-capable model with explicit route and effort (or honestly
reported inherited effort). Do not inherit the most expensive model merely from
the primary session. Escalate only a named unresolved finding or capability gap
after a cheaper attempt; quota exhaustion is an availability failure, not a
capability failure.

Before dispatch, validate a request with `render_gate.py review-preflight`.
Record exact pages, family representatives, omitted-page rationale, reader tasks,
route and stopping condition. The command validates evidence and request shape;
the owner judges the adequacy of sampling and external evidence. It does not
intercept arbitrary native or shell launches, so invoking it remains mandatory
owner procedure. No all-page pass follows automatically at final delivery.

For a new repeated layout, inspect representative real-data pages covering dense
legends, long labels, signed or zero tails and other actual extremes. On
revision, inspect new layouts, affected family representatives, relevant flagged
pages and necessary neighbours. Expand within a family when a defect suggests
propagation; expand globally only for a demonstrated document-wide issue.
Explain an exhaustive request rather than using "final" or "pagination changed"
as the reason.

Carry exact accepted page rasters across page movement. Changed numbering or
footers do not prove changed body readability, but neither may they be silently
masked: verify composition, numbering and routes and unchanged body and source
placement separately, then record the bounded family recheck. Global typography
or scale changes reopen affected layout families, not numerical acceptance by
default.

## Review packet

The owner supplies the reader's question, assumed knowledge, intended viewing
size, required comparisons, applicable scientific and display constraints and
exact artifact identity. For visual review, supply labelled PNG or JPEG pages
and overview contact sheets generated from that PDF, not the PDF itself. Prepare
the images in a scratch directory outside the repository. Retain the source PDF,
renderer and revision, and hash in session evidence so temporary images can be
reconstructed.
Include the relevant reference page or pages, labelled as references with their
own artifact identity, and the plot contract's concrete acceptance features and
justified departures. Do not ask reviewers to reconstruct the standard from an
adjective such as "polished" or from the candidate alone.

State whether images belong to one deliverable or are independent alternative
designs. Withhold the expected winner, not this essential scope. Supply adjacent
pages for continuity judgments. Include required series, undefined-bin handling,
uncertainty and scale constraints: visual criticism cannot authorize removing
flavours, masking inconvenient bins, clipping ranges or changing denominators.

For a substantial artifact, an independent reviewer first receives this packet
without the author's self-assessment or expected verdict. It is not blind to
requirements or necessary scientific context. After its first findings, provide
the author's rationale and reconcile disagreements against the artifact. Do not
ask the reviewer to confirm that an already declared improvement is good.

## Figure and page tasks

Before making visual findings, the reviewer must confirm actual pixel access and
identify a visible page-specific feature. An image tool's success message alone
is not evidence of access. If pixels are absent, stop and return **not
assessed**; the owner verifies the raster files and supplies images through a
working route. Do not infer observations from the brief, filenames or source.

Report two distinct results: **reference fidelity** (the applicable acceptance
features and justified departures) and **reading-task success** (the tasks
below). Neither a clipping check nor a numerical pass replaces these results.

For each family, identify the actual panels used to answer these questions:

- What is being compared? Trace a relevant series from its legend entry through
  the main panel and any reference or ratio panel. Can it be followed where
  curves overlap, without decoding several weak cues at once? Check draw-order
  occlusion; a series hidden by an identical curve differs from a missing series.
  Request an enlarged crop or source check before concluding.
- Which feature communicates the effect? Can the reader see its location and
  direction, tail and support, and the displayed uncertainty? Does the scale
  help? Inspect all displayed series before attributing a range to a particular
  spike or tail. A range needed to contain the data is not itself a defect;
  distinguish required support from an optional presentation tradeoff.
- Can the necessary alternatives be compared without avoidable page turns? Is
  separation clarifying a comparison or merely reflecting the rendering loop?
- At final placement, can labels, tick values, legend glyphs and captions be
  read? Do annotations collide with borders, other text or relevant data? Are
  long labels clipped? Does a sparse page leave its plots unnecessarily small? A
  large empty area is a defect; the render gate's `page-blank-band` check
  measures it.
- Does the plot stand on its own? The legend and colour key sit inside the plot,
  axis labels name the compared quantities, a plot whose reading is not obvious
  has a how-to-read note pointing to the report, and no task-specific term is
  undefined. (This applies where the plotbook is read before the report.)
- Does each row and column have a consistent role? Are unique comparisons
  missing, duplicated or broken across page boundaries? Inventory checks
  corroborate this. Within one deliverable, are encodings stable or intentional
  changes clearly identified? Do not judge alternative versions as pages of one
  book.

Inspect selected pages individually at the declared normal reading size; use
relevant contact sheets for sequence and composition and enlarged crops to
resolve suspected defects. Generate full contact-sheet coverage mechanically; do
not force a reviewer to ingest all sheets when unchanged sequence evidence
already exists. Record selected pages, family coverage and render size. If an
image is too small to judge a feature, return **not assessed** and request the
appropriate render. Do not infer readability from successful text extraction,
source settings, high DPI metadata or a tiny contact sheet. Grayscale checks are
diagnostics for contrast and encoding, not a requirement to replace all color
cues.

Line styles and marker shapes may help or hurt. Name the observed interaction
(for example short dash segments disappearing at final size, or marker clutter
masking the band) rather than imposing a blanket ban. Do not recommend a new
palette or template without explaining the reader problem it solves.

## Companion comprehension tasks

The copy reviewer reads the complete source and reader brief. Without access to
the working-session narrative, it reconstructs the question, principal findings,
reasoning and limits. For each material finding, it identifies what comparison
supports it and the exact delivered figure or page route. It explains one
difficult distinction in the report's own terms and flags missing steps or
definitions needed to do so. The owner checks these routes against the final
PDFs and the numerical and source record.

Ask whether the report assumes knowledge of the investigation rather than the
reader's domain knowledge. Can a brief transition or one worked example replace
repeated caveats? Are methods, observations and interpretation in the order
needed to understand them? Does the lookup material locate evidence or repeat
the argument? Apply the form rules of [report-writing](../../report-writing/SKILL.md)
where it defines them (form order, aids first; headlines, choices and colour).
Mark every paragraph the reader would need to re-read to follow and name the aid
that should carry it: a plot, sketch or diagram, a commented equation, a list or
a table. Identify any ordered process, parallel chain or population comparison
still left to prose. Check that each section opens with its headline, every
choice put to the reader is a choice box with a recommendation, an alternative
and evidence links, definitions sit beside their first use, and no evidence claim
rests on a session record. Report concrete locations and the proposed aid.

The reviewer may require structural revision even when individual sentences are
correct. It must not expand a concise companion into a tutorial simply to explain
every familiar term. The reader brief controls explanatory depth.

## Findings and revision

When presentation feedback exposes a problem, search the owning source and
mechanical inventory for the same cause before patching the named example;
inspect affected family representatives and adjacent reading tasks. This is not
an instruction to reread every page. Record the scope and findings in the
existing review record. Fix ordinary presentation choices autonomously within the
confirmed contract; escalate conflicts with user preferences or changes in
scientific meaning. This diagnostic pass does not require a full rerender or
another approval round for every local correction; recheck the affected scope
under the rules below.

Record findings in the existing session review record, not a new bureaucracy:

| Field | Required content |
| --- | --- |
| Location | Exact PDF/hash, page/panel or source section |
| Observation | What is visibly present or what explanatory step is missing |
| Reader impact | Which task fails, is ambiguous, or takes needless searching |
| Correction | Smallest coherent change; may include splitting, merging or rewriting |
| Recheck | New artifact identity, inspected scope, resolved/unresolved/not assessed |

Separate observed defects, uncertain observations and optional preferences.
An agreement with user criticism is not evidence of inspection; a pass must name
the task and artifact examined. The primary checks visual allegations against
the rendered image before accepting them. A reviewer can be wrong in either
direction: false reassurance and invented defects both require correction.
Corroborate page and panel inventories mechanically. Resolve uncertain labels,
markers or ratio-domain allegations against a readable crop and, where needed,
the owning source and numerical evidence; a raster impression does not establish
statistical semantics. Record the disposition, including reviewer mistakes,
without silently converting an uncertain observation into a pass or defect.

Mechanical checks catch bounds, missing panels, unexpected labels or inconsistent
glyphs; they do not certify communication. Do not use a single numerical quality
score to conceal these distinctions. The [render gate](workflow.md) runs these
checks before visual review.

Fix affected figures and pages and repeat bounded reviews. Global layout, scale
or typography changes reopen affected families; pagination reopens navigation
and composition checks. Preserve unrelated accepted evidence. A GO with optional
cosmetics remains GO; do not start a polish, rebuild and review cycle unless it
solves a material reader problem or the user requests it. Finish when tasks
succeed and material findings are resolved, not after a fixed number of
iterations. Record residual limitations and retain human-review status.
