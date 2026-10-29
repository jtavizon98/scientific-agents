# Scientific implementation

## Ownership and framework composition

Keep what the field's shared framework already provides in that framework's
layer, and put your own combinations of stable objects in the analysis layer.
Where two definitions of one quantity may legitimately differ, make the
difference explicit. Share common mathematics rather than duplicating formulas.

In high-energy physics (HEP), for example, the framework layer holds official
detector calibrations and the per-object corrections ("decorations") attached
to it, and the analysis layer holds your event selection. "Reconstruction-level"
quantities come from the measured detector response and "particle-level"
quantities from the simulated true particles before the detector; the two are
defined separately on purpose.

Use framework-native configuration as the visible execution plan. Keep human
scientific choices and stage composition visible; separate host paths from
scientific definitions where supported. Prefer native includes or composition.
Generate repetitive catalogs only from a frozen, validated source, retain or
reconstruct the generated artifact, and check determinism. When a framework
requires duplication, use a validator rather than inventing a preprocessor.

Avoid managers, registries, factories, callbacks, and workflow engines unless
the framework requires them or they remove real duplication without hiding the
scientific procedure.

## Numerical evidence

For personal scripts and small libraries, acceptance is led by intended-data
or artifact execution and inspection of numerical results and plots. Keep a
small suite for scientific invariants and demonstrated bugs a plausible plot
could conceal. Scale tests to risk and reuse, not production-software ceremony
or a test-count target.

Short recipes primarily need real-artifact execution and review. Reusable
numerical helpers need independently calculated examples. Select relevant cases
(the last two items use HEP vocabulary; the others apply in any field):

- exact cut boundaries, exclusivity, object filtering/order, equal-value ties,
  and systematic reordering;
- candidate selection and assignment ties;
- units, wrapped angles, masses, rapidity, and transverse quantities;
- missing collections, invalid values, empty inputs, and unavailable slots;
- negative weights, zero signed normalization, ratio denominators;
- accounting for every item on each side of a comparison: matched, present
  only in the measurement (in HEP, "fake") or only in the truth ("missed");
- underflow, overflow, nonuniform bins, and, for a response matrix, which axis
  is truth and which is measured ("response orientation").

A regression test must fail against the known incorrect behavior it guards.
Mirroring the formula under test is not an independent oracle. Avoid tests of
source wording, import allowlists, internal call structure, or an evolving CLI
without a demonstrated requirement. Exhaustive malformed-input testing for a
fixed repository-owned artifact is rarely useful scientific protection.

Run affected checks during iteration and required suites at a coherent
integration checkpoint. Broaden or repeat checks for new changes, failures,
or unresolved concerns. Identify unavailable runtime validation explicitly.

## Performance

For performance-sensitive work, record wall time, peak RSS, input size, host,
CPU allocation, I/O location, and command. Agree the allowed regression before
the rewrite. Preserve single-pass, bounded-memory, lazy, vectorized, or compiled
execution where measurements justify it.

Isolate optimization behind a domain-named function and compare against a clear
reference. Add caching, concurrency, code generation, or serialization only for
an observed bottleneck or required recovery property. Unexplained regression
blocks the performance claim even when outputs agree.

## Validation order

Check each stage before the ones that depend on it, so an upstream error is
not mistaken for a downstream one. For a data-analysis pipeline, use the
applicable stages in dependency order (a cutflow, item 4, is the table of how
many events, raw and weighted, survive each selection step):

1. Source identity and event accounting.
2. Schema, units, identity, and object multiplicities.
3. Factor-level weights and normalization.
4. Raw and weighted cutflows.
5. Inclusive object and event distributions.
6. Regions, overlaps, yields, and observables.
7. Systematic paths and coverage.
8. Response, acceptance, efficiency, closure, and stress tests.
9. Final results and covariance.

A downstream match cannot excuse an upstream mismatch. Preserve numerical
evidence in machine-readable form when it is needed to reproduce the acceptance
comparison. Plots help interpretation; they do not replace exact result contracts.
