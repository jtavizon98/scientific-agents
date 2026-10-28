---
name: scientific-coding
description: Write, revise, or reconstruct scientific code with readable scientific stages, sourced reasons for meaningful changes, and numerical evidence. Use for scientific scripts, libraries, analysis configuration, and traceable rewrites; scale the record and validation to the task.
---

# Scientific coding

Make the scientific transformation and the reasons for its implementation
inspectable. Read the owning repository's instructions, scientific sources,
current implementation, and relevant workflow. Preserve native framework
conventions and the user's scope. Follow the project's decision and domain
review requirements; this skill does not approve a scientific choice.

## Choose the depth

- Small change: explain its reason, cite the supporting evidence, run the
  relevant check, and update the existing rationale where behavior changed.
  Do not create a ledger or report merely for using this skill.
- Substantial implementation or rewrite: establish the stage contract below,
  keep a concise logical-change record in the code repository, and give the
  reader a walkthrough of the resulting implementation.
- Explicit historical reconstruction: additionally read
  [Reconstruct a trace](references/reconstruction.md). Retain exact ancestry,
  patches, and evidence sufficient to reconstruct the requested lineage.

For substantial work, read [Scientific implementation](references/implementation.md)
before designing or editing. For a small change, consult its relevant section
only when validation, framework composition, or performance needs guidance.

## Establish the scientific contract

Before substantial implementation, identify the question, authoritative source,
owning repository and layer, input/output artifacts, named stages, invariants,
units and boundaries, expected scale, validation oracle, and acceptance evidence.
Record a performance baseline and regression gate when performance matters.
State non-goals. Reuse the project's decision record rather than creating a
parallel policy document. Resolve material scientific and architectural choices
under its decision process before implementing them.

## Expose the procedure

Keep the top-level path in scientific execution order. Name intermediate values
and helpers after physical or mathematical meaning. Give each formula, selection,
weight, normalization, binning, and response convention one implementation owner.
Independent diagnostic oracles may check that owner without becoming a second
canonical implementation.

Split a stage when it has its own contract, reuse, or useful direct tests. Keep
a short linear transformation together when splitting would obscure it.
Prefer native framework configuration and thin domain adapters over a wrapper
framework. Comments explain choices, sources, units, conventions, and measured
performance constraints, rather than restating syntax.

## Explain meaningful changes

For each logical change, retain enough information to answer:

- What changed, and where is the actual diff or before/after implementation?
- Why was it needed: scientific choice, source requirement, observed defect,
  runtime evidence, framework constraint, performance measurement, or readability?
- What source supports that reason, and which parts are inference or a new decision?
- What behavior should change or remain invariant?
- What check was performed, what happened, and what remains unverified?

Use precise source locations and artifact identities where needed to recover
the evidence. A passing test does not establish a historical motive or prove
that a scientific definition is correct. Say when a reason is unknown; do not
turn a plausible explanation into recorded history.

Keep enduring rationale next to the owning code or configuration, with longer
decisions in existing repository documentation. For substantial work, use its
existing change/decision record, or a concise Markdown record in its documentation
area if none exists. Link each entry to the actual diff, source, and result.
Git commits can support that record when committing is authorized; this skill
does not require a commit. Session records own commands, logs, attempts, and
handoffs. Link evidence instead of copying it into several ledgers.

## Verify and hand back

Use focused checks for logical changes and full framework runs at behavior-changing
milestones. Run relevant real artifacts and inspect numerical outputs and plots;
retain small independent cases for scientific invariants and demonstrated bugs.
Do not preserve obsolete expectations after an intentional definition change.

Compare upstream identities and accounting before accepting downstream agreement.
Preserve failures and clearly limit claims to the inputs, modes, and scale tested.
For substantial work, explain the entry point, ordered stages, formula owners,
framework wiring, checks, extension points, performance, and remaining gaps.
A concise repository walkthrough is enough unless a separate report was requested.
