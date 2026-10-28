# Evidence for scientific figure review

The rendering library and the review process have different responsibilities.
Keep your renderer; expose enough evidence to check what it produced.

| Evidence | Producer | What it can establish |
| --- | --- | --- |
| Numerical source and independent check | Analysis | Defined quantities and calculations agree for tested inputs |
| Printed-value manifest | Typesetting step | Expected formatted values occur in the rendered artifact |
| Figure checks | Renderer/save step | Detected clipping, overlap or undersized text |
| Page/panel inventory | Composition loop | Expected figures and navigation match the composed artifact |
| Artifact and input hashes | Producer/checker | Evidence refers to these exact bytes |
| Reading-task review | Reviewer inspecting pixels | Selected final pages communicate the intended comparison |

No row substitutes for another. Hashes establish identity, not correctness.
The optional supplied [render checker](render-review.md) implements mechanical
checks and an explicit review preflight. Its printed matcher checks text and row context, not arbitrary table-cell
semantics. Visual agreement is not a numerical oracle.

## analyb route

The existing library provides `figcheck`, `printed`, `makelatex` page maps and
`provenance`. Figure checks are opt-in; an import alone does not run them.
The current supported evidence formats in that checker are
`analyb.figcheck` v1, `analyb.printed_values` v4 and `analyb.plotbook_page_map` v1.
Use the exact matching rule and schema supported by the pinned checker/library
pair. The [example requirements](../examples/custom-plotting/requirements-analyb.txt)
pin the reviewed public snapshot used in this extraction, not a moving branch.

## Other renderers

Inspect your existing evidence before adding anything. Emit values at formatting
time so recorded text matches the number printed. Include source identities and
enough context to distinguish repeated values. Emit page maps in the same loop
that places panels. Regenerate sidecars when their figure changes.

For a pipeline that cannot express its inventory in the supported schema, use
an explicit equivalent check with artifact-bound evidence. Record what was
checked and any coverage gaps. Do not label an applicable check not applicable
solely because an adapter is missing.

## Review and revision

Run programmatic checks on the final composed artifact before assigning visual
reading tasks. A lone successful lint command does not prove that numbers,
inventory or source claims were assessed. Select changed layouts, dense examples
and representatives of repeated figure families; document what sampling covers.
Use actual reading-size pages, with enlarged crops for uncertain details.

Carry accepted evidence forward only when identity and relevant dependencies
remain valid. Recomposition may require checking placement/navigation without
rechecking unchanged scientific calculations. Changing normalization or the
denominator does require scientific review, even when the plot looks similar.

Stylistic thresholds and preferred palettes are defaults to adapt, not universal
scientific truths. Distinguish correctness failures, presentation findings and
human-approved exceptions in the record.
