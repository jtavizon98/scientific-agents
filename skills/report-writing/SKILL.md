---
name: report-writing
description: Use when creating, extending, restructuring, or reviewing substantial reports, papers, technical notes, LaTeX sources, or PDF deliverables. Guides whole-artifact structure, evidence, copy review, build checks and visual review; does not install enforcement or reviewer tools.
---

# Report Writing

Treat a report as a designed explanation, not an append-only record. Find and
read the project's owning report-production or writing workflow before editing;
that workflow is authoritative when it conflicts with this skill. If the project
has none, use this skill with the [source-library](../../workflows/source-library.md)
and [render-review](../../workflows/render-review.md) procedures and agree the
deliverable/checks in the existing task brief. A full report-production procedure
is still being extracted; do not invent a private workspace dependency.

`copy-reviewer` below names a read-only independent reviewer role, not an installed
tool. Use an available agent or human with that capability. Visual review needs
actual access to rendered pixels; builds need the project's real toolchain. If a
required capability is unavailable, record the gap and hand it to the user rather
than substituting self-review or marking the gate passed. Copying this skill does
not configure agents, permissions, build tools or automatic checks.

## Start with the whole artifact

Define the audience, question, intended use, status, and authoritative evidence.
For an existing report, establish the whole argument from source, contents,
evidence and prior review. During local revisions reuse that orientation and
inspect affected source/pages rather than rereading unchanged material.

For a substantial explanatory report, also define the reader's knowledge base:

- record what subject matter, terminology, mathematics, and tools the report may
  assume;
- identify the reader's preferred coursework, references, or existing
  documentation;
- list unfamiliar or domain-specific methods that require motivation before
  use;
- distinguish standard sourced methods from custom diagnostics or extensions.

Keep this reader model in a durable project or session artifact and reference
it from the report plan and active state. Do not leave it only in conversation,
where compaction or interruption can remove it. In the report, connect methods
to the reader's known sources where they are introduced. If a necessary method
is absent from that knowledge base, explain why it is needed, derive its role at
the appropriate level, and cite an additional authoritative source.

Choose and state one edit mode before writing:

- **Patch:** the organizing model works and the change is local.
- **Structural revision:** the argument works but its content needs
  consolidation or reordering.
- **Rewrite:** the organizing model no longer answers the reader's question.

Do not preserve text merely to minimize changed lines. Repetition, stale
conclusions, chronology in place of explanation, and tables at the wrong unit
of comparison are structural defects.

## Choose form by scope

Use a memo for one bounded question, an article for one continuous study, and a
book for several dependent questions or substantial durable reference
material. Use the lightest form that gives the reader a clear route through the
material. Never force a substantial report into a minimal template.

Outline content roles before drafting. Keep present conclusions in the main
argument; move exhaustive catalogues, provenance, chronology, and superseded
interpretations to appendices or a journal. Keep source data separate from
presentation when tables are generated or repeated.

## Write and review

For a plotbook companion, establish coverage and a provisional argument early,
but settle the figure comparisons and composed layout before final prose and page
routes. Follow the project's plotting workflow. If writing exposes a missing
comparison, reopen figure design and recheck affected claims/navigation. Identify
both final report and plotbook versions and the plotbook page map; do not duplicate
its catalogue as report prose.

Assume the reader's domain knowledge, not participation in the working sessions.
Explain the question, evidence and finding in the order needed to follow the
reasoning. Introduce populations before ratios and methods before results. Use
brief transitions or one worked example where needed; a concise companion should
not grow into a tutorial by default. Give recurring conventions and lookup
material clear homes. Neither page counts nor historical layouts are universal.

Preserve observation, inference, decision, and proposal as distinct claims.
After the complete draft exists, perform a coherence pass that can delete,
merge, move, or rewrite material.

For substantial collaborator-facing reports:

1. Use a diagnostic copy review before editing when the existing structure is
   suspect.
2. Use the read-only `copy-reviewer` on the complete draft. Supply the reader
   brief and artifact before the author's verdict. Ask it to reconstruct the
   question, findings, supporting comparisons and limits without the session
   narrative. Permit structural revision even when sentences are individually
   correct. Check each material claim's route to the delivered evidence separately.
3. Resolve its findings through the primary writing owner.
4. Validate factual, numerical, and domain claims separately.
5. Compile the source and inspect warnings.
6. Run available programmatic render checks over the complete artifact before
   visual delegation. Account for applicable build, geometry, printed-value,
   inventory and navigation checks; absent checks are not assessed. Follow the
   project's preflight contract when provided. Select residual reading tasks on
   new/changed layouts, family representatives and relevant flags. Use an explicit
   economy image-capable route, not an inherited expensive primary model. Supply
   selected reading-size rasters, useful contacts and ambiguous-detail crops,
   never a PDF. Final delivery does not require another exhaustive page pass.

Visual review must test reading tasks at final placement, not merely check for
overlap. Contact sheets show organization, not small-text readability. Inspect
selected final pages at the intended reading size, and enlarge ambiguous
details. Record artifact identity, page, observed problem, reader impact and
recheck result; mark features that cannot be judged as not assessed. Distinguish
defects from optional preferences and verify reviewer allegations against the
artifact. Agreement with the author or user is not evidence of inspection.

Iterate figures and the complete document as needed. Split, consolidate or
reorder when that improves the reader's task; preserve coverage. Colors, line
styles and markers are context-dependent tools. Stop when material findings are
resolved and reading tasks work, not after a fixed number of passes or speculative
cosmetic changes. Escalate only decisions outside the confirmed contract.

Preserve accepted evidence after corrections. Repagination reopens navigation
and composition, not every page's readability; global styling changes reopen
affected layout families. Record sampling without claiming unseen pages were
inspected. Escalate model or scope only for a concrete unresolved problem. A GO
with optional cosmetics stays GO. Use source, parsed
text, and the copy reviewer for document structure and content; visual review
is for rendered appearance.

The copy reviewer does not replace source, physics, numerical, or visual
validation. Short internal notes may skip independent copy review unless the
brief requires it.

## Finish

Confirm that the opening states the question, scope, status, and conclusion;
terms precede their use; each important claim has one primary home; tables and
figures answer the prose's comparisons; history does not compete with current
truth; method explanations match the durable reader knowledge base; and the
rendered artifact has actually been inspected through bounded raster images.
